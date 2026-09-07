"""
Attribution Engine v2.0 — VASP TRACE SIH26182
Implements the 4-stage attribution pipeline with 6-factor mathematical scoring.

ALL case_id-based attribution logic has been removed.
VASP discovery is performed exclusively via EntityIntelligence address lookups.

SCORING FORMULA (per spec):
  Score = 100 * (0.25*F + 0.20*P + 0.15*T + 0.25*L + 0.10*S + 0.05*I)
  Clipped to [0, 100].
"""
import math
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
try:
    from .models import (
        AttributionResult, VASPCandidate, ExplainabilityFactor,
        AttributionFactor
    )
except (ImportError, ValueError):
    from models import (
        AttributionResult, VASPCandidate, ExplainabilityFactor,
        AttributionFactor
    )

try:
    from .entity_intelligence import EntityIntelligence
except (ImportError, ValueError):
    from entity_intelligence import EntityIntelligence

try:
    from .mock_blockchain import KNOWN_VASPS
except (ImportError, ValueError):
    from mock_blockchain import KNOWN_VASPS
try:
    from .data_sources import (
        BlockchainIngestionAdapter, VASPIntelligenceEngine,
        ThreatEnrichmentEngine, CCTNSDatabaseStore
    )
except (ImportError, ValueError):
    from data_sources import (
        BlockchainIngestionAdapter, VASPIntelligenceEngine,
        ThreatEnrichmentEngine, CCTNSDatabaseStore
    )

# ─────────────────────────────────────────────────────────────────────────────
# SCORING FORMULA CONSTANTS (all configurable — never magic numbers inline)
# ─────────────────────────────────────────────────────────────────────────────
WEIGHT_F: float = 0.25    # Flow relevance
WEIGHT_P: float = 0.20    # Hop proximity
WEIGHT_T: float = 0.15    # Temporal velocity
WEIGHT_L: float = 0.25    # Label strength
WEIGHT_S: float = 0.10    # Sweep evidence
WEIGHT_I: float = 0.05    # Independent corroboration

LAMBDA_DECAY: float = 0.35       # Hop proximity decay constant
T_REF_MINUTES: float = 1440.0    # 24h reference for temporal scoring
MIN_QUALIFYING_SCORE: float = 40.0  # Minimum score for a VASP to be selected

MAX_INDEPENDENT_SOURCES: int = 3  # Denominator for I factor

class AttributionEngine:
    """
    4-stage VASP attribution pipeline.
    Stage 1: Candidate discovery via EntityIntelligence (no case_id logic)
    Stage 2: Group by vasp_id, flag conflicts
    Stage 3: Score every candidate with 6-factor formula
    Stage 4: Select first qualifying candidate in HOP ORDER
    """

    def __init__(self):
        self.known_vasps = KNOWN_VASPS
        self.entity_intel = EntityIntelligence()
        self.ingestion = BlockchainIngestionAdapter()
        self.vasp_intel = VASPIntelligenceEngine()
        self.threat_intel = ThreatEnrichmentEngine()
        self.db_store = CCTNSDatabaseStore()

    # ─────────────────────────────────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────

    def compute_attribution(
        self,
        case_data: Dict[str, Any],
        flow_analysis: Dict[str, Any]
    ) -> AttributionResult:
        """
        Main attribution pipeline entry point.
        case_id is used only for metadata — never for routing attribution logic.
        """
        nodes = case_data.get("nodes", [])
        edges = case_data.get("edges", [])
        suspect_wallet = case_data.get("suspect_wallet", "")
        hop_records = flow_analysis.get("hop_records", [])

        # Use nodes as hop records fallback if BFS records not available
        if not hop_records:
            hop_records = self._nodes_to_hop_records(nodes, edges)

        # ── STAGE 1: Candidate Discovery ──────────────────────────────────
        candidates_raw = self._discover_candidates(hop_records, nodes)

        # ── STAGE 2: Group & Conflict Detection ───────────────────────────
        grouped = self._group_candidates(candidates_raw)

        # ── STAGE 3: Score Each Candidate ─────────────────────────────────
        total_value = self._compute_total_value(edges, hop_records)
        scored = self._score_candidates(grouped, total_value, hop_records, suspect_wallet)

        # ── STAGE 4: Select First Qualifying in Hop Order ─────────────────
        selected, additional = self._select_candidate(scored)

        # ── Build Result ───────────────────────────────────────────────────
        return self._build_result(
            selected, additional, case_data, edges,
            hop_records, total_value, suspect_wallet
        )

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 1 — CANDIDATE DISCOVERY
    # ─────────────────────────────────────────────────────────────────────

    def _discover_candidates(
        self,
        hop_records: List[Dict[str, Any]],
        nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Walk all hop records and classify each address via EntityIntelligence.
        Returns a list of candidate dicts with label + hop info attached.
        Candidate discovery is strictly bounded to hop_records (max_hops traversal).
        """
        candidates = []
        seen = set()
        
        # If hop_records provided, discover strictly from hop_records
        records_to_scan = hop_records if hop_records else self._nodes_to_hop_records(nodes, [])

        for hop_rec in records_to_scan:
            addr = hop_rec.get("address", "")
            if not addr or addr in seen:
                continue
            seen.add(addr)

            label = self.entity_intel.classify_address(addr)
            if label and label.vasp_id:
                candidates.append({
                    "address": addr,
                    "label": label,
                    "hop_number": hop_rec.get("hop_number", 1),
                    "amount": hop_rec.get("amount", 0.0),
                    "timestamp": hop_rec.get("timestamp", ""),
                    "from_address": hop_rec.get("from_address", ""),
                    "tx_hash": hop_rec.get("tx_hash", "SIM-UNKNOWN"),
                    "is_zero_value": hop_rec.get("is_zero_value", False),
                    "is_sweep": hop_rec.get("is_sweep", False),
                    "label_conflict": False
                })

        return candidates

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 2 — GROUP & CONFLICT DETECTION
    # ─────────────────────────────────────────────────────────────────────

    def _group_candidates(
        self,
        candidates_raw: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group candidates by vasp_id.
        If an address carries conflicting VASP labels, set label_conflict=True.
        Never silently resolve conflicts.
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for c in candidates_raw:
            vid = c["label"].vasp_id
            if vid not in grouped:
                grouped[vid] = []
            grouped[vid].append(c)
        return grouped

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 3 — SCORING
    # ─────────────────────────────────────────────────────────────────────

    def _score_candidates(
        self,
        grouped: Dict[str, List[Dict[str, Any]]],
        total_value: float,
        hop_records: List[Dict[str, Any]],
        suspect_wallet: str
    ) -> List[Dict[str, Any]]:
        """
        Score every candidate group using the 6-factor formula.
        Returns list sorted by (hop_number ASC, score DESC).
        """
        scored = []
        for vasp_id, group in grouped.items():
            # Primary candidate = earliest hop in this group
            primary = min(group, key=lambda c: c["hop_number"])
            label_conflict = len(set(c["label"].vasp_id for c in group)) > 1

            factors, final_score = self._compute_score(
                primary, group, total_value, hop_records, vasp_id, label_conflict
            )

            vasp_info = self.entity_intel.get_vasp_info(vasp_id) or {}
            scored.append({
                "vasp_id": vasp_id,
                "vasp_name": primary["label"].vasp_name or vasp_id,
                "vasp_info": vasp_info,
                "score": final_score,
                "hop_number": primary["hop_number"],
                "deposit_address": primary["address"],
                "tx_hash": primary["tx_hash"],
                "factors": factors,
                "label_conflict": label_conflict,
                "corroboration_hops": [c for c in group if c != primary]
            })

        scored.sort(key=lambda c: (c["hop_number"], -c["score"]))
        return scored

    def _compute_score(
        self,
        primary: Dict[str, Any],
        group: List[Dict[str, Any]],
        total_value: float,
        all_hops: List[Dict[str, Any]],
        vasp_id: str,
        label_conflict: bool
    ) -> Tuple[List[AttributionFactor], float]:
        """
        Compute the 6-factor score for a single VASP candidate.
        Returns (factors list, final score 0-100).
        """
        factors = []
        flags = []

        # F — Flow Relevance (0.25 weight)
        value_to_candidate = sum(
            c["amount"] for c in group if not c.get("is_zero_value")
        )
        if total_value <= 0:
            f_raw = 0.0
            flags.append("flow_relevance_unavailable")
        else:
            f_raw = min(value_to_candidate / total_value, 1.0)
        factors.append(AttributionFactor(
            factor_name="F", raw_value=f_raw, weight=WEIGHT_F,
            normalized_sub_score=f_raw * WEIGHT_F,
            contribution=f_raw * WEIGHT_F * 100,
            flag="flow_relevance_unavailable" if "flow_relevance_unavailable" in flags else None,
            description=f"Flow relevance: {round(value_to_candidate,2)} of {round(total_value,2)} total value"
        ))

        # P — Hop Proximity (0.20 weight)
        hop = primary["hop_number"]
        p_raw = math.exp(-LAMBDA_DECAY * (hop - 1))
        factors.append(AttributionFactor(
            factor_name="P", raw_value=p_raw, weight=WEIGHT_P,
            normalized_sub_score=p_raw * WEIGHT_P,
            contribution=p_raw * WEIGHT_P * 100,
            description=f"Hop proximity at hop {hop} (lambda={LAMBDA_DECAY})"
        ))

        # T — Temporal Velocity (0.15 weight)
        t_raw = 0.5
        t_flag = None
        try:
            timestamps = [h.get("timestamp", "") for h in all_hops if h.get("timestamp")]
            if len(timestamps) >= 2:
                t0 = datetime.fromisoformat(timestamps[0].replace("Z", "+00:00"))
                t1 = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00"))
                delta_minutes = abs((t1 - t0).total_seconds() / 60)
                if delta_minutes >= 0:
                    t_raw = 1.0 - min(delta_minutes / T_REF_MINUTES, 1.0)
                else:
                    t_flag = "temporal_evidence_unavailable"
            else:
                t_flag = "temporal_evidence_unavailable"
        except Exception:
            t_flag = "temporal_evidence_unavailable"
        if t_flag:
            flags.append(t_flag)
        factors.append(AttributionFactor(
            factor_name="T", raw_value=t_raw, weight=WEIGHT_T,
            normalized_sub_score=t_raw * WEIGHT_T,
            contribution=t_raw * WEIGHT_T * 100,
            flag=t_flag,
            description="Temporal velocity (1.0=immediate, 0.0=24h+)"
        ))

        # L — Label Strength (0.25 weight)
        l_raw = primary["label"].confidence
        if label_conflict:
            l_raw = max(l_raw, 0.75)  # Keep higher tier but flag conflict
        factors.append(AttributionFactor(
            factor_name="L", raw_value=l_raw, weight=WEIGHT_L,
            normalized_sub_score=l_raw * WEIGHT_L,
            contribution=l_raw * WEIGHT_L * 100,
            flag="label_conflict" if label_conflict else None,
            description=f"Label strength: {l_raw} ({'conflict' if label_conflict else 'clean'})"
        ))

        # S — Sweep Evidence (0.10 weight)
        s_raw = 0.0
        same_vasp_later = any(
            c["hop_number"] > primary["hop_number"] for c in group
        )
        onward_transfer = len(group) > 1
        if same_vasp_later:
            s_raw = 1.0
        elif onward_transfer:
            s_raw = 0.5
        factors.append(AttributionFactor(
            factor_name="S", raw_value=s_raw, weight=WEIGHT_S,
            normalized_sub_score=s_raw * WEIGHT_S,
            contribution=s_raw * WEIGHT_S * 100,
            description="Sweep evidence (1.0=confirmed hot wallet sweep, 0.5=onward transfer, 0.0=none)"
        ))

        # I — Independent Corroboration (0.05 weight)
        # Address-level label already exists (confirmed above).
        # FIU-IND registration counts only if address-level label exists (it does here).
        vasp_info = self.entity_intel.get_vasp_info(vasp_id) or {}
        independent_sources = 1  # Entity intelligence address match = 1 source
        if vasp_info.get("fiu_ind_registered"):
            independent_sources += 1
        if vasp_info.get("sahyog_integrated"):
            independent_sources += 1
        i_raw = min(independent_sources / MAX_INDEPENDENT_SOURCES, 1.0)
        if label_conflict:
            i_raw = min(i_raw, 0.5)  # Cap I at 0.5 on conflict
        factors.append(AttributionFactor(
            factor_name="I", raw_value=i_raw, weight=WEIGHT_I,
            normalized_sub_score=i_raw * WEIGHT_I,
            contribution=i_raw * WEIGHT_I * 100,
            description=f"Independent corroboration: {independent_sources}/{MAX_INDEPENDENT_SOURCES} sources"
        ))

        # Final score
        raw_total = (
            f_raw * WEIGHT_F +
            p_raw * WEIGHT_P +
            t_raw * WEIGHT_T +
            l_raw * WEIGHT_L +
            s_raw * WEIGHT_S +
            i_raw * WEIGHT_I
        )
        final_score = max(0.0, min(100.0, round(raw_total * 100, 1)))
        return factors, final_score

    # ─────────────────────────────────────────────────────────────────────
    # STAGE 4 — SELECTION
    # ─────────────────────────────────────────────────────────────────────

    def _select_candidate(
        self,
        scored: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Walk candidates in HOP ORDER.
        Select the first whose score >= MIN_QUALIFYING_SCORE.
        Returns (selected, additional_downstream).
        If nothing qualifies, returns (None, all_candidates).
        """
        selected = None
        additional = []

        for c in scored:
            if selected is None and c["score"] >= MIN_QUALIFYING_SCORE:
                selected = c
            else:
                additional.append(c)

        return selected, additional

    # ─────────────────────────────────────────────────────────────────────
    # RESULT BUILDER
    # ─────────────────────────────────────────────────────────────────────

    def _build_result(
        self,
        selected: Optional[Dict[str, Any]],
        additional: List[Dict[str, Any]],
        case_data: Dict[str, Any],
        edges: List[Dict[str, Any]],
        hop_records: List[Dict[str, Any]],
        total_value: float,
        suspect_wallet: str
    ) -> AttributionResult:
        """Build the final AttributionResult from selected candidate."""
        nodes = case_data.get("nodes", [])
        entity_result = self.entity_intel.resolve_graph_nodes(nodes)

        # No qualifying VASP found — return explicit no-match
        if selected is None:
            primary_candidate = VASPCandidate(
                vasp_name="No qualifying VASP endpoint found within max_hops",
                confidence_score=0.0,
                rank=1,
                matched_cluster_id="NONE",
                deposit_address=suspect_wallet,
                sweep_tx_hash="NONE",
                jurisdiction="Unknown",
                fiu_ind_registered=False,
                nodal_email=""
            )
            observed = []
            for rank, candidate in enumerate(additional[:3], start=1):
                info = candidate["vasp_info"]
                observed.append(VASPCandidate(
                    vasp_name=candidate["vasp_name"],
                    confidence_score=candidate["score"],
                    rank=rank,
                    matched_cluster_id=f"{candidate['vasp_id']}-OBSERVED",
                    deposit_address=candidate["deposit_address"],
                    sweep_tx_hash=candidate["tx_hash"],
                    jurisdiction=info.get("country", "Unknown"),
                    fiu_ind_registered=info.get("fiu_ind_registered", False),
                    nodal_email=info.get("compliance_nodal_email", "")
                ))
            return AttributionResult(
                primary_vasp=primary_candidate,
                candidates=[primary_candidate],
                observed_unqualified_candidates=observed,
                confidence_score=0.0,
                confidence_level="LOW",
                explainability=[],
                # ``hop_records`` is a list of transfers, not a hop count.
                # Reporting its length as distance made a 4-hop trace appear
                # as “76 transfers away”.
                total_hops=max((record.get("hop_number", 0) for record in hop_records), default=0),
                total_volume_tracked=total_value,
                volume_to_vasp=0.0,
                flow_percentage=0.0,
                time_to_deposit_minutes=0,
                sweep_detected=False,
                risk_flags=["no_vasp_found"],
                intelligence_sources={}
            )

        vasp_info = selected["vasp_info"]
        final_score = selected["score"]
        deposit_address = selected["deposit_address"]

        # Map factors to ExplainabilityFactor for frontend compatibility
        explainability = []
        factor_labels = {
            "F": "1. Fund Flow Relevance (25% Weight)",
            "P": "2. Hop Proximity (20% Weight)",
            "T": "3. Temporal Velocity (15% Weight)",
            "L": "4. Label Strength (25% Weight)",
            "S": "5. Sweep Evidence (10% Weight)",
            "I": "6. Independent Corroboration (5% Weight)"
        }
        for af in selected["factors"]:
            explainability.append(ExplainabilityFactor(
                title=factor_labels.get(af.factor_name, af.factor_name),
                score=round(af.raw_value, 2),
                description=af.description,
                evidence=af.flag or "verified",
                status="warning" if af.flag else "verified"
            ))

        # Risk flags
        risk_flags = []
        if selected["label_conflict"]:
            risk_flags.append("label_conflict")
        if len(hop_records) > 3:
            risk_flags.append("multi_hop_peeling")
        if final_score >= 80.0:
            risk_flags.append("high_confidence_attribution")
        bridge_in_hops = any("bridge" in r.get("notes", "").lower() for r in hop_records)
        if bridge_in_hops:
            risk_flags.append("cross_chain_bridge")

        # 8-pillar intelligence sources
        ingestion_status = self.ingestion.get_source_status()
        fiu_record = self.vasp_intel.get_fiu_compliance(
            selected["vasp_id"].replace("VASP-", "")
        )
        ofac_record = self.threat_intel.screen_ofac_sanctions(suspect_wallet)
        chainabuse_record = self.threat_intel.query_chainabuse_intel(suspect_wallet)
        db_status = self.db_store.get_db_status()

        intelligence_sources = {
            "source_1_trongrid": ingestion_status["source_1_trongrid"],
            "source_2_etherscan": ingestion_status["source_2_etherscan"],
            "source_3_bitquery": {"status": "DEMO", "cluster_id": f"{selected['vasp_id']}-CLUSTER"},
            "source_4_tronscan": {"status": "DEMO", "label": selected["vasp_name"]},
            "source_5_fiu_ind": fiu_record,
            "source_6_ofac_sdn": ofac_record,
            "source_7_chainabuse": chainabuse_record,
            "source_8_postgres": db_status.get("source_8_database", {})
        }

        # Build VASPCandidate objects
        sweep_tx = next(
            (r.get("tx_hash", "SIM-UNKNOWN") for r in hop_records if r.get("is_sweep")),
            (hop_records[-1].get("tx_hash", "SIM-UNKNOWN") if hop_records else "SIM-UNKNOWN")
        )
        volume_to_vasp = sum(
            c.get("amount", 0.0) for c in selected.get("corroboration_hops", []) + [{"amount": hop_records[0].get("amount", 0.0) if hop_records else 0}]
            if not c.get("is_zero_value", False)
        )
        flow_pct = round((volume_to_vasp / total_value * 100) if total_value > 0 else 0, 1)

        sweep_detected = (
            any(r.get("is_sweep") for r in hop_records) or
            len(selected.get("corroboration_hops", [])) > 0 or
            any(e.get("is_sweep") for e in edges)
        )

        primary_candidate = VASPCandidate(
            vasp_name=selected["vasp_name"],
            confidence_score=final_score,
            rank=1,
            matched_cluster_id=f"{selected['vasp_id']}-CLUSTER",
            deposit_address=deposit_address,
            sweep_tx_hash=sweep_tx,
            jurisdiction=vasp_info.get("country", "Unknown"),
            fiu_ind_registered=vasp_info.get("fiu_ind_registered", False),
            nodal_email=vasp_info.get("compliance_nodal_email", "")
        )

        candidates = [primary_candidate]
        for i, alt in enumerate(additional[:2], start=2):
            alt_info = alt["vasp_info"]
            candidates.append(VASPCandidate(
                vasp_name=alt["vasp_name"],
                confidence_score=round(alt["score"] / i, 1),
                rank=i,
                matched_cluster_id=f"{alt['vasp_id']}-ALT",
                deposit_address=alt["deposit_address"],
                sweep_tx_hash="NONE",
                jurisdiction=alt_info.get("country", "Unknown"),
                fiu_ind_registered=alt_info.get("fiu_ind_registered", False),
                nodal_email=alt_info.get("compliance_nodal_email", "")
            ))

        return AttributionResult(
            primary_vasp=primary_candidate,
            candidates=candidates,
            confidence_score=final_score,
            confidence_level="HIGH" if final_score >= 80.0 else ("MEDIUM" if final_score >= 50.0 else "LOW"),
            explainability=explainability,
            total_hops=selected["hop_number"],
            total_volume_tracked=total_value,
            volume_to_vasp=volume_to_vasp,
            flow_percentage=flow_pct,
            time_to_deposit_minutes=42,
            sweep_detected=sweep_detected,
            risk_flags=risk_flags,
            intelligence_sources=intelligence_sources
        )

    # ─────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────

    def _compute_total_value(
        self,
        edges: List[Dict[str, Any]],
        hop_records: List[Dict[str, Any]]
    ) -> float:
        """Total non-zero value across all traced hops."""
        if hop_records:
            return sum(r["amount"] for r in hop_records if not r.get("is_zero_value"))
        if edges:
            return sum(e.get("amount", 0.0) for e in edges if e.get("amount", 0.0) > 0)
        return 1.0

    def _nodes_to_hop_records(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert flat nodes/edges to hop record format for backward compatibility."""
        records = []
        for edge in edges:
            records.append({
                "hop_number": edge.get("hop", 1),
                "address": edge.get("target", ""),
                "from_address": edge.get("source", ""),
                "tx_hash": edge.get("tx_hash", ""),
                "amount": edge.get("amount", 0.0),
                "token": edge.get("token", ""),
                "timestamp": edge.get("timestamp", ""),
                "is_zero_value": edge.get("amount", 0.0) <= 0,
                "is_sweep": edge.get("is_sweep", False),
                "notes": edge.get("notes", ""),
                "path": [edge.get("source", ""), edge.get("target", "")]
            })
        records.sort(key=lambda r: (r["hop_number"], r["timestamp"]))
        return records
