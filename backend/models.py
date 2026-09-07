from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# v2.0 PROVIDER LAYER MODELS
# ─────────────────────────────────────────────────────────────────────────────

class NormalizedTransaction(BaseModel):
    """A blockchain transaction normalized to a chain-agnostic format."""
    tx_id: str                        # SIM-xxxxxxxx for demo; real hash for live
    from_address: str
    to_address: str
    amount: float
    token: str
    timestamp: str
    block_height: Optional[int] = None
    is_demo_synthetic: bool = True    # Always True in demo mode
    chain: str = "Unknown"
    source_provider: str = "SyntheticDemoProvider"
    retrieved_at: str = ""
    response_sha256: str = ""

class AddressLabel(BaseModel):
    """Intelligence label resolved for a blockchain address."""
    address: str
    label: str                        # e.g. "CoinDCX Hot Wallet", "Unknown", "Mixer"
    vasp_id: Optional[str] = None     # e.g. "VASP-COINDCX" if matched
    vasp_name: Optional[str] = None
    entity_type: str = "unknown"      # vasp_hot, deposit, mule, suspect, mixer, bridge, unknown
    confidence: float = 0.0           # 0.0 to 1.0

class EntityIntelligenceResult(BaseModel):
    """Result of entity intelligence classification for a set of addresses."""
    vasp_matched: bool = False
    matched_vasp_id: Optional[str] = None
    matched_vasp_name: Optional[str] = None
    matched_vasp_info: Optional[Dict[str, Any]] = None
    deposit_address: Optional[str] = None
    vasp_hot_address: Optional[str] = None
    address_labels: List[AddressLabel] = []
    jurisdiction: str = "Unknown"
    fiu_ind_registered: bool = False
    nodal_email: str = ""

class NodeData(BaseModel):
    id: str
    label: str
    type: str  # suspect, mule, mixer, bridge, deposit, vasp_hot, cold_storage
    chain: str
    balance: Optional[str] = "0.00"
    risk_score: int = 0
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    entity_name: Optional[str] = None
    tags: List[str] = []
    case_ids: List[str] = []
    is_shared: bool = False

class EdgeData(BaseModel):
    id: str
    source: str
    target: str
    amount: float
    token: str
    tx_hash: str
    timestamp: str
    hop: int
    is_sweep: bool = False
    notes: Optional[str] = None

class GraphPayload(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class ExplainabilityFactor(BaseModel):
    title: str
    score: float
    description: str
    evidence: str
    status: str  # verified, warning, info

class VASPCandidate(BaseModel):
    vasp_name: str
    confidence_score: float
    rank: int
    matched_cluster_id: str
    deposit_address: str
    sweep_tx_hash: str
    jurisdiction: str
    fiu_ind_registered: bool
    nodal_email: str

class AttributionResult(BaseModel):
    primary_vasp: VASPCandidate
    candidates: List[VASPCandidate]
    # Labels that were observed on a reachable path but did not meet the
    # attribution threshold.  These are leads, never a basis for action.
    observed_unqualified_candidates: List[VASPCandidate] = []
    confidence_score: float
    confidence_level: str  # HIGH, MEDIUM, LOW
    explainability: List[ExplainabilityFactor]
    total_hops: int
    total_volume_tracked: float
    volume_to_vasp: float
    flow_percentage: float
    time_to_deposit_minutes: int
    sweep_detected: bool
    risk_flags: List[str] = []  # Added for frontend badges (nested_service, cross_chain_bridge, etc.)
    intelligence_sources: Dict[str, Any] = {}  # Ingested 8-pillar intelligence metadata

class CrossCaseAlert(BaseModel):
    has_shared_infrastructure: bool
    shared_wallet_address: Optional[str] = None
    linked_case_ids: List[str] = []
    linked_case_titles: List[str] = []
    police_stations: List[str] = []
    syndicate_risk_multiplier: float = 1.0
    notes: str = ""

class SahyogRequest(BaseModel):
    request_id: str
    case_id: str
    vasp_name: str
    target_wallet: str
    recommended_action: str  # FREEZE_PRESERVATION, KYC_DISCLOSURE, TRANSACTION_LOGS
    legal_section: str  # Section 94 BNSS 2023 / Section 106 BNSS 2023 / PMLA 2002
    urgency: str  # IMMEDIATE, HIGH, STANDARD
    fiu_nodal_officer: str
    crypto_amount: str
    inr_equivalent: str
    status: str  # DRAFT, DISPATCHED, ACKNOWLEDGED, ASSETS_FROZEN
    timestamp: str
    dispatch_receipt_hash: Optional[str] = None
    eligible_for_dispatch: bool = False
    eligibility_reason: str = "Requires evidence review"
    investigation_run_id: Optional[str] = None

class ForensicReport(BaseModel):
    report_id: str
    case_id: str
    case_title: str
    investigating_officer: str
    police_station: str
    chain: str
    suspect_wallet: str
    attributed_vasp: str
    confidence: float
    sha256_hash: str
    generated_at: str
    section_63_bsa_certified: bool = True
    # section_65b_certified removed — BSA 2023 Section 63 is the operative provision

# ─────────────────────────────────────────────────────────────────────────────
# v2.0 ATTRIBUTION FACTOR MODEL (per-factor scoring breakdown)
# ─────────────────────────────────────────────────────────────────────────────

class AttributionFactor(BaseModel):
    """Per-factor breakdown for full explainability of attribution scoring."""
    factor_name: str          # F, P, T, L, S, I
    raw_value: float          # Raw computed value before weighting
    weight: float             # e.g. 0.25 for F
    normalized_sub_score: float   # raw_value * weight
    contribution: float       # contribution to final 0-100 score
    flag: Optional[str] = None    # e.g. "temporal_evidence_unavailable"
    description: str = ""

# ─────────────────────────────────────────────────────────────────────────────
# v2.0 EVIDENCE INTEGRITY MANIFEST
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceIntegrityManifest(BaseModel):
    """
    Tamper-evident technical integrity record for a forensic investigation run.
    NOT a legal certificate. NOT court-admissible evidence on its own.
    This is a cryptographic integrity seal for the data pipeline output.
    """
    investigation_run_id: str
    case_id: str
    suspect_wallet: str
    chain: str
    source_provider: str              # e.g. "SyntheticDemoProvider"
    retrieval_timestamp: str
    transaction_hashes: List[str]     # All tx IDs in the trace
    path_summary: str
    sha256_seal: str                  # SHA-256 of canonical payload
    is_synthetic: bool = True         # True = demo data, False = live
    integrity_status: str = "TAMPER_EVIDENT_TECHNICAL_RECORD"
    disclaimer: str = (
        "This is a tamper-evident technical integrity record generated by VASP TRACE. "
        "It is NOT a Section 63 BSA 2023 certificate and NOT court-admissible evidence "
        "on its own. It must be accompanied by authorized investigator attestation."
    )

# ─────────────────────────────────────────────────────────────────────────────
# v2.0 SUGGESTED LAWFUL ACTION (SAHYOG / BNSS)
# ─────────────────────────────────────────────────────────────────────────────

class SuggestedLawfulAction(BaseModel):
    """
    A suggested (not automated) lawful action for an authorized investigator.
    Requires human review and authorized legal process before any action is taken.
    """
    legal_reference: str        # e.g. "Section 94 BNSS 2023"
    title: str                  # e.g. "Summons to Produce Document/Thing"
    target_vasp: str
    target_address: str
    relevant_transactions: List[str] = []
    supporting_evidence_ref: str = ""
    request_type: str           # KYC_DISCLOSURE / FREEZE_PRESERVATION / TRANSACTION_LOGS
    status: str = "DRAFT — requires authorized investigator/legal process review"
    caveat: str = (
        "This is a system-generated draft only. No account freezing or asset seizure "
        "is initiated by this system. All actions require authorized investigator "
        "review and proper legal process under applicable law."
    )

# ─────────────────────────────────────────────────────────────────────────────
# v2.0 DATABASE PREPARATION MODELS (no PostgreSQL wired yet — schema prep only)
# ─────────────────────────────────────────────────────────────────────────────

class DBCase(BaseModel):
    """Maps to future 'cases' table."""
    case_id: str
    fir_number: str
    police_station: str
    investigating_officer: str
    stolen_amount_inr: float
    chain: str
    suspect_wallet: str
    status: str = "ACTIVE"
    created_at: str = ""

class DBWallet(BaseModel):
    """Maps to future 'wallets' table."""
    address: str
    chain: str
    vasp_id: Optional[str] = None
    entity_type: str = "unknown"
    first_seen: str = ""

class DBAttributionEvidence(BaseModel):
    """Maps to future 'attribution_evidence' table."""
    run_id: str
    case_id: str
    candidate_vasp_id: str
    score: float
    hop_number: int
    is_selected: bool = False
    factors_json: str = "{}"    # JSON-serialized List[AttributionFactor]
    created_at: str = ""
