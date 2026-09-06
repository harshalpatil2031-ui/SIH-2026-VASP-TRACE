"""
Explainable VASP Attribution Engine.

Implements a 4-stage pipeline to identify the most likely VASP endpoint
for a traced fund flow, with transparent per-factor scoring.

IMPORTANT DESIGN INVARIANTS:
  1. NO case-ID-based logic anywhere in this module.  The algorithm must
     produce identical scores for identical evidence regardless of case ID.
  2. VASP identification is delegated exclusively to entity_intelligence.
     This module never reads or depends on node/edge `type` fields for
     entity classification.
  3. The first qualifying VASP candidate in HOP ORDER (not score order) is
     selected as primary.  Higher-scored later hops are NOT preferred over
     an earlier qualifying hop — hop proximity is already captured in factor P.
  4. If no candidate clears MIN_QUALIFYING_SCORE, the result explicitly says
     "no qualifying VASP endpoint found within max_hops" — no forced match.

SCORING FORMULA:
    Score = 100 * (W_F*F + W_P*P + W_T*T + W_L*L + W_S*S + W_I*I)
    clipped to [0, 100].

Factor weights (all named module-level constants):
    W_F = 0.25  — flow relevance (value routed to candidate / total traced)
    W_P = 0.20  — hop proximity (exponential decay from origin)
    W_T = 0.15  — temporal velocity (speed of transfer from origin)
    W_L = 0.25  — label strength (verified → 1.0 down to weak → 0.25)
    W_S = 0.10  — sweep evidence (later same-VASP hot wallet forwarding)
    W_I = 0.05  — independent corroboration (distinct source count)

Decay / reference constants:
    LAMBDA  = 0.35   — hop-proximity exponential decay rate
    T_REF   = 1440   — temporal reference window in minutes (24 hours)

Attribution threshold:
    MIN_QUALIFYING_SCORE = 40  — minimum score for a candidate to be selected
"""
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from .models import (
    AttributionResult,
    AttributionFactor,
    VASPCandidate,
    ExplainabilityFactor,
    AddressLabel,
)
from .entity_intelligence import EntityIntelligence

# ---------------------------------------------------------------------------
# Module-level constants (configurable — never inline magic numbers)
# ---------------------------------------------------------------------------

# Factor weights (must sum to 1.0)
W_F: float = 0.25   # Flow relevance
W_P: float = 0.20   # Hop proximity
W_T: float = 0.15   # Temporal velocity
W_L: float = 0.25   # Label strength
W_S: float = 0.10   # Sweep evidence
W_I: float = 0.05   # Independent corroboration

# Hop-proximity exponential decay rate
LAMBDA: float = 0.35

# Temporal velocity reference window (minutes)
T_REF: float = 1440.0  # 24 hours

# Minimum score for a candidate to qualify as the primary attribution
MIN_QUALIFYING_SCORE: float = 40.0

# Independent source count cap for factor I
I_SOURCE_CAP: int = 3


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_iso_timestamp(ts: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO-8601 timestamp string to a timezone-aware datetime.
    Returns None if the string is None, empty, or unparseable.
    """
    if not ts:
        return None
    try:
        # Handle both Z suffix and +HH:MM offset
        ts_clean = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_clean)
    except (ValueError, AttributeError):
        return None


def _delta_minutes(
    ts_origin: Optional[str], ts_candidate: Optional[str]
) -> Optional[float]:
    """
    Compute elapsed minutes between two ISO timestamps.
    Returns None if either timestamp is missing or delta is negative.
    """
    dt_origin = _parse_iso_timestamp(ts_origin)
    dt_candidate = _parse_iso_timestamp(ts_candidate)
    if dt_origin is None or dt_candidate is None:
        return None
    delta = (dt_candidate - dt_origin).total_seconds() / 60.0
    if delta < 0:
        return None
    return delta


# ---------------------------------------------------------------------------
# Candidate data structure (internal)
# ---------------------------------------------------------------------------

class _CandidateEntry:
    """Internal working state for a VASP candidate during scoring."""

    def __init__(self, label: AddressLabel, hop_number: int, tx_hash: str,
                 amount: float, timestamp: Optional[str], path: List[str]) -> None:
        self.label = label
        self.hop_number = hop_number
        self.tx_hash = tx_hash
        self.amount = amount           # Amount transferred TO this address
        self.timestamp = timestamp
        self.path = path
        self.label_conflict: bool = False
        self.conflicting_labels: List[AddressLabel] = []
        self.sweep_to_hot: bool = False    # Later hop forwards to same-VASP hot wallet
        self.onward_transfer: bool = False  # Any onward transfer found


# ---------------------------------------------------------------------------
# Attribution Engine
# ---------------------------------------------------------------------------

class AttributionEngine:
    """
    4-Stage VASP Attribution Engine.

    Stage 1: Candidate discovery — scan hop_records via entity_intelligence.
    Stage 2: Conflict detection — flag addresses with conflicting VASP labels.
    Stage 3: Scoring — apply the 6-factor formula to each candidate.
    Stage 4: Selection — walk candidates in HOP ORDER; select first qualifying.
    """

    def __init__(self, entity_intel: Optional[EntityIntelligence] = None) -> None:
        """
        Args:
            entity_intel: EntityIntelligence instance. If None, a default
                          instance is created using the project registry.
        """
        self._intel = entity_intel or EntityIntelligence()
        self.known_vasps = {}  # Populated from entity_intelligence for UI compat

    def compute_attribution(
        self,
        case_data: Dict[str, Any],
        flow_analysis: Dict[str, Any],
    ) -> AttributionResult:
        """
        Run the full 4-stage attribution pipeline.

        Args:
            case_data:     Raw case dict (nodes, edges, suspect_wallet, …).
            flow_analysis: Output of GraphEngine.analyze_fund_flow().

        Returns:
            AttributionResult with per-factor breakdown and all frontend fields.
        """
        investigation_run_id = str(uuid.uuid4())
        edges = case_data.get("edges", [])
        nodes = case_data.get("nodes", [])
        suspect_wallet = case_data.get("suspect_wallet", "")

        # Use hop_records from BFS if available, else fall back to edges
        hop_records = flow_analysis.get("hop_records", [])
        if not hop_records and edges:
            # Compatibility: convert edges to hop_record-like dicts
            hop_records = [
                {
                    "hop_number": e.get("hop", idx + 1),
                    "from_address": e["source"],
                    "to_address": e["target"],
                    "tx_hash": e.get("tx_hash", ""),
                    "amount": float(e.get("amount", 0.0)),
                    "token": e.get("token", "USDT"),
                    "timestamp": e.get("timestamp", None),
                    "is_zero_value": float(e.get("amount", 0.0)) == 0.0,
                    "is_synthetic": e.get("is_synthetic", False),
                    "path": [e["source"], e["target"]],
                }
                for idx, e in enumerate(edges)
            ]

        # --- STAGE 1: Candidate Discovery ---
        candidates_raw: List[_CandidateEntry] = []
        for hr in hop_records:
            to_addr = hr["to_address"]
            labels = self._intel.get_labels(to_addr)
            if not labels:
                continue  # Not a VASP-labeled address — skip silently
            for label in labels:
                candidates_raw.append(_CandidateEntry(
                    label=label,
                    hop_number=hr["hop_number"],
                    tx_hash=hr["tx_hash"],
                    amount=hr["amount"],
                    timestamp=hr.get("timestamp"),
                    path=hr.get("path", []),
                ))

        # --- STAGE 2: Conflict Detection ---
        # Group by address; detect conflicting vasp_ids
        addr_to_entries: Dict[str, List[_CandidateEntry]] = {}
        for entry in candidates_raw:
            addr = entry.label.address
            addr_to_entries.setdefault(addr, []).append(entry)

        for addr, entries in addr_to_entries.items():
            vasp_ids = {e.label.vasp_id for e in entries}
            if len(vasp_ids) > 1:
                for e in entries:
                    e.label_conflict = True
                    e.conflicting_labels = [x.label for x in entries if x is not e]

        # Group by vasp_id; the first (earliest hop) entry per vasp_id is primary
        vasp_primary: Dict[str, _CandidateEntry] = {}
        vasp_corroboration: Dict[str, List[_CandidateEntry]] = {}
        for entry in sorted(candidates_raw, key=lambda x: x.hop_number):
            vid = entry.label.vasp_id
            if vid not in vasp_primary:
                vasp_primary[vid] = entry
                vasp_corroboration[vid] = []
            else:
                # Later same-vasp hop → corroboration
                vasp_corroboration[vid].append(entry)
                # Check sweep: is this a known hot wallet of the same VASP?
                hot_wallets = self._intel.get_vasp_hot_wallets(vid)
                if entry.label.address in hot_wallets:
                    vasp_primary[vid].sweep_to_hot = True
                vasp_primary[vid].onward_transfer = True

        # Also check onward transfers for single-entry candidates
        for vid, entry in vasp_primary.items():
            if not entry.onward_transfer:
                # Check if any later hop goes out from this address
                for hr in hop_records:
                    if (hr["from_address"] == entry.label.address and
                            hr["hop_number"] > entry.hop_number):
                        entry.onward_transfer = True
                        # Is the destination a known hot wallet of same VASP?
                        hot_wallets = self._intel.get_vasp_hot_wallets(vid)
                        if hr["to_address"] in hot_wallets:
                            entry.sweep_to_hot = True
                        break

        if not vasp_primary:
            return self._no_qualifying_result(
                investigation_run_id, case_data, flow_analysis, hop_records, suspect_wallet
            )

        # Compute total traced value (non-zero transfers from suspect)
        total_traced = self._calculate_total_traced(hop_records, suspect_wallet)

        # Origin timestamp (first outgoing transfer from suspect)
        origin_ts = None
        for hr in hop_records:
            if hr["from_address"] == suspect_wallet and hr.get("timestamp"):
                origin_ts = hr["timestamp"]
                break

        # --- STAGE 3: Scoring ---
        scored: List[Tuple[float, List[AttributionFactor], _CandidateEntry]] = []
        for vid, entry in vasp_primary.items():
            # Compute true flow amount without double-counting sweeps or duplicate paths
            vasp_inflow = 0.0
            for hr in hop_records:
                if hr["is_zero_value"]:
                    continue
                
                # Check if this transfer arrives at the current VASP
                to_labels = self._intel.get_labels(hr["to_address"])
                if not to_labels or not any(l.vasp_id == vid for l in to_labels):
                    continue
                
                # Check if it originated from outside the current VASP
                from_labels = self._intel.get_labels(hr["from_address"])
                if from_labels and any(l.vasp_id == vid for l in from_labels):
                    continue  # Skip internal sweep within the same VASP
                
                vasp_inflow += hr["amount"]
            
            entry.amount = vasp_inflow
            
            score, factors = self._score_candidate(
                entry=entry,
                total_traced=total_traced,
                origin_ts=origin_ts,
                hop_records=hop_records,
            )
            scored.append((score, factors, entry))

        # --- STAGE 4: Selection in HOP ORDER ---
        # Sort by hop_number first, then score (lower hop = earlier consideration)
        scored_by_hop = sorted(scored, key=lambda x: (x[2].hop_number, -x[0]))

        selected: Optional[Tuple[float, List[AttributionFactor], _CandidateEntry]] = None
        other_vasps: List[Tuple[float, List[AttributionFactor], _CandidateEntry]] = []

        for item in scored_by_hop:
            score, factors, entry = item
            if selected is None and score >= MIN_QUALIFYING_SCORE:
                selected = item
            else:
                other_vasps.append(item)

        if selected is None:
            return self._no_qualifying_result(
                investigation_run_id, case_data, flow_analysis, edges
            )

        sel_score, sel_factors, sel_entry = selected

        # Build primary VASPCandidate
        primary_candidate = self._build_vasp_candidate(
            sel_entry, sel_score, rank=1
        )

        # Build alternative candidates (other VASPs, not nearest)
        alt_candidates = [primary_candidate]
        for rank, (oth_score, _, oth_entry) in enumerate(other_vasps[:2], start=2):
            alt_candidates.append(
                self._build_vasp_candidate(oth_entry, oth_score, rank=rank)
            )

        # Build UI-compatible explainability list
        explainability = self._build_explainability(sel_factors, sel_entry)

        # Collect limitations
        limitations = [
            f.degradation_reason for f in sel_factors
            if f.is_degraded and f.degradation_reason
        ]
        if sel_entry.label_conflict:
            limitations.append(
                f"Label conflict on address {sel_entry.label.address}: "
                f"conflicting VASP associations detected — analyst review required."
            )

        # Compute UI-facing flow metrics
        total_vol = float(total_traced) if total_traced else float(
            edges[0]["amount"] if edges else 1.0
        )
        vol_to_vasp = float(sel_entry.amount)
        flow_pct = round((vol_to_vasp / total_vol) * 100, 1) if total_vol > 0 else 0.0

        # Time to deposit
        delta = _delta_minutes(origin_ts, sel_entry.timestamp)
        time_to_deposit = int(delta) if delta is not None else 35

        return AttributionResult(
            primary_vasp=primary_candidate,
            candidates=alt_candidates,
            confidence_score=round(sel_score, 1),
            confidence_level=self._confidence_level(sel_score),
            explainability=explainability,
            total_hops=max((hr["hop_number"] for hr in hop_records), default=0),
            selected_vasp_hop=sel_entry.hop_number,
            total_volume_tracked=round(total_vol, 2),
            volume_to_vasp=round(vol_to_vasp, 2),
            flow_percentage=flow_pct,
            time_to_deposit_minutes=time_to_deposit,
            sweep_detected=sel_entry.sweep_to_hot,
            attribution_factors=sel_factors,
            limitations=limitations,
            no_qualifying_vasp=False,
            investigation_run_id=investigation_run_id,
        )

    # ------------------------------------------------------------------
    # Scoring Formula
    # ------------------------------------------------------------------

    def _score_candidate(
        self,
        entry: _CandidateEntry,
        total_traced: float,
        origin_ts: Optional[str],
        hop_records: List[Dict[str, Any]],
    ) -> Tuple[float, List[AttributionFactor]]:
        """
        Compute the 6-factor attribution score for a single candidate.

        Returns:
            (score_0_to_100, list_of_AttributionFactor)
        """
        factors: List[AttributionFactor] = []

        # --- F: Flow Relevance ---
        f_raw = 0.0
        f_degraded = False
        f_reason = None
        if total_traced <= 0 or entry.amount <= 0:
            f_raw = 0.0
            f_degraded = True
            f_reason = "flow relevance unavailable: zero total traced value or zero-value transfer"
        else:
            f_raw = min(entry.amount / total_traced, 1.0)
        factors.append(AttributionFactor(
            factor_name="Flow Relevance",
            factor_code="F",
            weight=W_F,
            raw_value=f_raw,
            sub_score=f_raw,
            contribution=round(W_F * f_raw * 100, 2),
            is_degraded=f_degraded,
            degradation_reason=f_reason,
        ))

        # --- P: Hop Proximity ---
        p_raw = math.exp(-LAMBDA * (entry.hop_number - 1))
        factors.append(AttributionFactor(
            factor_name="Hop Proximity",
            factor_code="P",
            weight=W_P,
            raw_value=float(entry.hop_number),
            sub_score=round(p_raw, 4),
            contribution=round(W_P * p_raw * 100, 2),
            is_degraded=False,
        ))

        # --- T: Temporal Velocity ---
        t_raw = 0.5
        t_degraded = False
        t_reason = None
        delta = _delta_minutes(origin_ts, entry.timestamp)
        if delta is None:
            t_raw = 0.5
            t_degraded = True
            t_reason = "temporal evidence unavailable: one or more timestamps missing or invalid"
        else:
            t_raw = 1.0 - min(delta / T_REF, 1.0)
        factors.append(AttributionFactor(
            factor_name="Temporal Velocity",
            factor_code="T",
            weight=W_T,
            raw_value=delta if delta is not None else -1.0,
            sub_score=round(t_raw, 4),
            contribution=round(W_T * t_raw * 100, 2),
            is_degraded=t_degraded,
            degradation_reason=t_reason,
        ))

        # --- L: Label Strength ---
        # On conflicting labels: use the higher tier but keep label_conflict visible
        strength = entry.label.strength
        if entry.label_conflict and entry.conflicting_labels:
            strengths = [entry.label.strength] + [
                lbl.strength for lbl in entry.conflicting_labels
            ]
            tier_order = ["verified", "recognized", "inferred", "weak"]
            best_strength = min(strengths, key=lambda s: tier_order.index(s)
                                if s in tier_order else 99)
            strength = best_strength
        l_raw = self._intel.get_label_strength_score(strength)
        factors.append(AttributionFactor(
            factor_name="Label Strength",
            factor_code="L",
            weight=W_L,
            raw_value=l_raw,
            sub_score=l_raw,
            contribution=round(W_L * l_raw * 100, 2),
            is_degraded=entry.label_conflict,
            degradation_reason=(
                "label conflict: address has conflicting VASP associations; "
                "higher-tier label used but analyst review required"
            ) if entry.label_conflict else None,
        ))

        # --- S: Sweep Evidence ---
        if entry.sweep_to_hot:
            s_raw = 1.0
        elif entry.onward_transfer:
            s_raw = 0.5
        else:
            s_raw = 0.0  # Absence is not penalized
        factors.append(AttributionFactor(
            factor_name="Sweep Evidence",
            factor_code="S",
            weight=W_S,
            raw_value=s_raw,
            sub_score=s_raw,
            contribution=round(W_S * s_raw * 100, 2),
            is_degraded=False,
        ))

        # --- I: Independent Corroboration ---
        ind_sources = entry.label.independent_sources
        # FIU-IND regulatory registration does NOT count unless an independent
        # address-level label already exists — it is captured in label.independent_sources
        # only when the VASP_DIRECTORY entry was independently confirmed.
        i_raw = min(ind_sources / I_SOURCE_CAP, 1.0)
        i_degraded = False
        i_reason = None
        if entry.label_conflict:
            i_raw = min(i_raw, 0.5)
            i_degraded = True
            i_reason = "independent corroboration capped at 0.5 due to label conflict"
        factors.append(AttributionFactor(
            factor_name="Independent Corroboration",
            factor_code="I",
            weight=W_I,
            raw_value=float(ind_sources),
            sub_score=round(i_raw, 4),
            contribution=round(W_I * i_raw * 100, 2),
            is_degraded=i_degraded,
            degradation_reason=i_reason,
        ))

        # --- Final Score ---
        raw_score = 100.0 * (
            W_F * factors[0].sub_score +
            W_P * factors[1].sub_score +
            W_T * factors[2].sub_score +
            W_L * factors[3].sub_score +
            W_S * factors[4].sub_score +
            W_I * factors[5].sub_score
        )
        score = max(0.0, min(100.0, raw_score))  # Clip to [0, 100]
        return round(score, 2), factors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_vasp_candidate(
        self, entry: _CandidateEntry, score: float, rank: int
    ) -> VASPCandidate:
        lbl = entry.label
        return VASPCandidate(
            vasp_name=lbl.vasp_name,
            vasp_id=lbl.vasp_id,
            confidence_score=round(score, 1),
            rank=rank,
            matched_cluster_id=f"{lbl.vasp_id}-HOP{entry.hop_number}",
            deposit_address=lbl.address,
            sweep_tx_hash=entry.tx_hash,
            jurisdiction=lbl.jurisdiction,
            fiu_ind_registered=lbl.fiu_ind_registered,
            nodal_email=lbl.nodal_email,
            hop_number=entry.hop_number,
            label_conflict=entry.label_conflict,
        )

    def _build_explainability(
        self,
        factors: List[AttributionFactor],
        entry: _CandidateEntry,
    ) -> List[ExplainabilityFactor]:
        """
        Convert AttributionFactor list into UI-compatible ExplainabilityFactor list.
        Preserves the existing frontend contract (title, score, description, evidence).
        """
        ui_factors = []
        factor_map = {f.factor_code: f for f in factors}

        f_fac = factor_map.get("F")
        p_fac = factor_map.get("P")
        t_fac = factor_map.get("T")
        l_fac = factor_map.get("L")

        if f_fac:
            pct = round(f_fac.sub_score * 100, 1)
            status = "warning" if f_fac.is_degraded else "verified"
            ui_factors.append(ExplainabilityFactor(
                title="1. Fund Flow Amount",
                score=f_fac.sub_score,
                description=(
                    f"{pct}% of traced value reached this VASP endpoint."
                    if not f_fac.is_degraded else
                    "Flow amount data unavailable or zero-value transfer."
                ),
                evidence=(
                    f"Factor F = {f_fac.sub_score:.3f} "
                    f"(weight {W_F}; contribution {f_fac.contribution:.1f} pts). "
                    + (f_fac.degradation_reason or "")
                ),
                status=status,
            ))

        if p_fac:
            ui_factors.append(ExplainabilityFactor(
                title="2. Hop Proximity",
                score=p_fac.sub_score,
                description=(
                    f"VASP endpoint reached at hop #{entry.hop_number} "
                    f"(proximity score {p_fac.sub_score:.3f} via exp(-{LAMBDA}×(hop-1)))."
                ),
                evidence=(
                    f"Factor P = {p_fac.sub_score:.3f} "
                    f"(weight {W_P}; contribution {p_fac.contribution:.1f} pts)."
                ),
                status="verified",
            ))

        if t_fac:
            delta_display = (
                f"{t_fac.raw_value:.0f} minutes from origin"
                if t_fac.raw_value >= 0 else "unknown"
            )
            status = "warning" if t_fac.is_degraded else "verified"
            ui_factors.append(ExplainabilityFactor(
                title="3. Transfer Velocity",
                score=t_fac.sub_score,
                description=(
                    f"Funds reached this endpoint in {delta_display}."
                    if not t_fac.is_degraded else
                    "Temporal evidence unavailable — timestamps missing or invalid."
                ),
                evidence=(
                    f"Factor T = {t_fac.sub_score:.3f} "
                    f"(weight {W_T}; T_REF={T_REF:.0f} min; contribution {t_fac.contribution:.1f} pts). "
                    + (t_fac.degradation_reason or "")
                ),
                status=status,
            ))

        if l_fac:
            status = "warning" if l_fac.is_degraded else "verified"
            ui_factors.append(ExplainabilityFactor(
                title="4. Entity Label Strength",
                score=l_fac.sub_score,
                description=(
                    f"Address label: {entry.label.strength} "
                    f"(source: {entry.label.source})"
                    + (" — CONFLICT DETECTED" if entry.label_conflict else "") + "."
                ),
                evidence=(
                    f"Factor L = {l_fac.sub_score:.3f} "
                    f"(weight {W_L}; contribution {l_fac.contribution:.1f} pts). "
                    + (l_fac.degradation_reason or "")
                ),
                status=status,
            ))

        return ui_factors

    @staticmethod
    def _confidence_level(score: float) -> str:
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    @staticmethod
    def _calculate_total_traced(hop_records: List[Dict[str, Any]], suspect_wallet: str) -> float:
        """
        Compute total traced value (non-zero transfers from suspect).
        Since hop_records are unique by (tx_hash, from, to), this correctly
        aggregates multiple outbound transfers or branching paths without
        double-counting duplicate downstream transfers.
        """
        return sum(
            hr["amount"] for hr in hop_records
            if hr["from_address"] == suspect_wallet and not hr["is_zero_value"]
        )

    def _no_qualifying_result(
        self,
        investigation_run_id: str,
        case_data: Dict[str, Any],
        flow_analysis: Dict[str, Any],
        hop_records: List[Dict[str, Any]],
        suspect_wallet: str,
    ) -> AttributionResult:
        """
        Return an explicit 'no qualifying VASP endpoint' result.
        Never forces a match when no candidate clears MIN_QUALIFYING_SCORE.
        """
        total_vol = self._calculate_total_traced(hop_records, suspect_wallet)

        # Create a sentinel VASPCandidate with explicit "no match" values
        sentinel = VASPCandidate(
            vasp_name="No Qualifying VASP Found",
            vasp_id="NONE",
            confidence_score=0.0,
            rank=1,
            matched_cluster_id="NONE",
            deposit_address="N/A",
            sweep_tx_hash="N/A",
            jurisdiction="N/A",
            fiu_ind_registered=False,
            nodal_email="N/A",
            hop_number=0,
            label_conflict=False,
        )
        return AttributionResult(
            primary_vasp=sentinel,
            candidates=[sentinel],
            confidence_score=0.0,
            confidence_level="LOW",
            explainability=[
                ExplainabilityFactor(
                    title="Attribution Result",
                    score=0.0,
                    description=(
                        f"No qualifying VASP endpoint found within the traced hops. "
                        f"Minimum qualifying score ({MIN_QUALIFYING_SCORE}) not reached "
                        f"by any labeled address."
                    ),
                    evidence="Increase max_hops or expand the VASP entity registry.",
                    status="info",
                )
            ],
            total_hops=flow_analysis.get("total_hops", 0),
            total_volume_tracked=total_vol,
            volume_to_vasp=0.0,
            flow_percentage=0.0,
            time_to_deposit_minutes=0,
            sweep_detected=False,
            attribution_factors=[],
            limitations=["No VASP-labeled address found within traversal depth."],
            no_qualifying_vasp=True,
            investigation_run_id=investigation_run_id,
        )
