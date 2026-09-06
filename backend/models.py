"""
Pydantic data models for VASP TRACE.
All request/response schemas and internal domain models are defined here.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# ---------------------------------------------------------------------------
# Graph / Case Domain Models
# ---------------------------------------------------------------------------

class NodeData(BaseModel):
    """Represents a single wallet node in the transaction graph."""
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
    """Represents a single on-chain transfer (hop) in the transaction graph."""
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
    is_synthetic: bool = False   # True for all synthetic/demo transactions
    is_zero_value: bool = False   # True when amount == 0


class GraphPayload(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Normalized Transaction (provider-agnostic, output of BlockchainProvider)
# ---------------------------------------------------------------------------

class NormalizedTransaction(BaseModel):
    """
    Provider-agnostic representation of a single on-chain transfer.
    All BlockchainProvider implementations must emit this type.
    """
    tx_id: str                   # Provider tx identifier (SIM-xxxx for synthetic)
    from_address: str
    to_address: str
    amount: float                # In token units (float; 0 is valid)
    token: str
    timestamp_iso: Optional[str] = None  # ISO-8601 UTC; None if unavailable
    block_number: Optional[int] = None
    is_synthetic: bool = False   # MUST be True for all demo/simulation records
    is_zero_value: bool = False   # Derived: amount == 0
    provider_request_id: Optional[str] = None  # Idempotency / audit key from provider
    raw: Optional[Dict[str, Any]] = None  # Original provider response (optional)


# ---------------------------------------------------------------------------
# Entity Intelligence Models
# ---------------------------------------------------------------------------

class AddressLabel(BaseModel):
    """
    A label associating a blockchain address with a known VASP entity.
    Multiple labels may exist for one address (e.g. conflicting sources).
    """
    address: str
    vasp_id: str                 # e.g. "VASP-COINDCX"
    vasp_name: str
    label_type: str              # "hot_wallet", "deposit_sweep", "cold_storage"
    strength: str                # "verified", "recognized", "inferred", "weak"
    source: str                  # "VASP_DIRECTORY", "BITQUERY", "TRONSCAN", etc.
    jurisdiction: str
    fiu_ind_registered: bool
    nodal_email: str
    independent_sources: int = 1  # Count of distinct independent sources confirming


# ---------------------------------------------------------------------------
# Attribution Engine Models
# ---------------------------------------------------------------------------

class VASPCandidate(BaseModel):
    """A candidate VASP endpoint identified during attribution."""
    vasp_name: str
    vasp_id: str = ""
    confidence_score: float
    rank: int
    matched_cluster_id: str
    deposit_address: str
    sweep_tx_hash: str
    jurisdiction: str
    fiu_ind_registered: bool
    nodal_email: str
    hop_number: int = 0
    label_conflict: bool = False  # True if address carries conflicting VASP labels


class AttributionFactor(BaseModel):
    """
    Per-factor breakdown of the attribution confidence score.
    Enables transparent, auditable explainability.
    """
    factor_name: str             # "flow_relevance", "hop_proximity", etc.
    factor_code: str             # F, P, T, L, S, I
    weight: float                # Module-level constant weight
    raw_value: float             # Raw computed value before normalization
    sub_score: float             # Normalized [0,1] sub-score
    contribution: float          # weight * sub_score * 100 (contribution to final)
    is_degraded: bool = False    # True when evidence is missing/partial
    degradation_reason: Optional[str] = None  # Human-readable limitation note


class ExplainabilityFactor(BaseModel):
    """Frontend-facing explainability card (preserved for UI compatibility)."""
    title: str
    score: float
    description: str
    evidence: str
    status: str  # verified, warning, info


class AttributionResult(BaseModel):
    """
    Complete attribution result including primary VASP identification,
    per-factor scoring breakdown, and human-readable limitations.
    All fields read by the existing frontend are preserved.
    """
    primary_vasp: VASPCandidate
    candidates: List[VASPCandidate]
    confidence_score: float
    confidence_level: str        # HIGH (>=70), MEDIUM (>=40), LOW (<40), NONE
    explainability: List[ExplainabilityFactor]
    total_hops: int
    selected_vasp_hop: int = 0
    total_volume_tracked: float
    volume_to_vasp: float
    flow_percentage: float
    time_to_deposit_minutes: int
    sweep_detected: bool

    # Extended fields (new — per-factor breakdown)
    attribution_factors: List[AttributionFactor] = []
    limitations: List[str] = []  # Human-readable list of evidence gaps / caveats
    no_qualifying_vasp: bool = False  # True when no candidate clears MIN_QUALIFYING_SCORE
    investigation_run_id: str = ""


# ---------------------------------------------------------------------------
# Evidence Integrity Manifest
# ---------------------------------------------------------------------------

class EvidenceIntegrityManifest(BaseModel):
    """
    Tamper-evident technical integrity record for a VASP attribution run.

    This is NOT a legal certificate, NOT described as court-admissible evidence,
    and NOT a Section 65B certificate. It is a cryptographic integrity check
    that allows verification that the data has not been modified after generation.
    """
    investigation_run_id: str
    case_id: str
    suspect_wallet: str
    chain: str
    source_provider: str
    provider_request_id: Optional[str]
    retrieval_timestamp_iso: str         # Part of hashed payload
    transaction_hashes: List[str]
    path_summary: str
    attribution_result_summary: str
    sha256_hash: str                     # Hash of the canonical hashed payload
    # --- Presentation-only metadata (NOT included in hash) ---
    display_timestamp: str               # Human-readable; outside hash boundary
    record_type: str = "TAMPER_EVIDENT_TECHNICAL_INTEGRITY_RECORD"


# ---------------------------------------------------------------------------
# Cross-Case Correlation Models
# ---------------------------------------------------------------------------

class CrossCaseAlert(BaseModel):
    """
    Result of cross-case infrastructure correlation analysis.
    Language deliberately uses 'shared infrastructure' and 'historical overlap',
    NOT 'syndicate detection' or 'proof of organized crime'.
    """
    has_shared_infrastructure: bool
    shared_wallet_address: Optional[str] = None
    linked_case_ids: List[str] = []
    linked_case_titles: List[str] = []
    police_stations: List[str] = []
    # Kept for API backward compat; semantically now "infrastructure_overlap_multiplier"
    syndicate_risk_multiplier: float = 1.0
    notes: str = ""
    analyst_review_required: bool = False


# ---------------------------------------------------------------------------
# Legal / SAHYOG Models
# ---------------------------------------------------------------------------

class SuggestedLawfulAction(BaseModel):
    """
    A suggested lawful action under BNSS 2023, generated as a DRAFT only.
    Requires authorized investigator and legal process review before use.
    """
    legal_reference: str          # e.g. "BNSS 2023 Section 94"
    title: str                    # e.g. "Summons to Produce Document/Thing"
    target_vasp: str
    target_address: str
    relevant_transactions: List[str] = []
    supporting_evidence_ref: str = ""
    request_type: str             # "KYC_DISCLOSURE", "TRANSACTION_LOGS", "PRESERVATION"
    status: str = "DRAFT — requires authorized investigator/legal process review"
    caveat: str = ""


class SahyogRequest(BaseModel):
    """SAHYOG protocol lawful requisition draft."""
    request_id: str
    case_id: str
    vasp_name: str
    target_wallet: str
    recommended_action: str  # KYC_DISCLOSURE, TRANSACTION_LOGS, PRESERVATION_REQUEST
    legal_section: str       # BNSS 2023 Section 94 / 106 / 107
    urgency: str             # IMMEDIATE, HIGH, STANDARD
    fiu_nodal_officer: str
    crypto_amount: str
    inr_equivalent: str
    status: str              # DRAFT_READY, DISPATCHED, ACKNOWLEDGED
    timestamp: str
    dispatch_receipt_hash: Optional[str] = None
    suggested_lawful_action: Optional[SuggestedLawfulAction] = None


# ---------------------------------------------------------------------------
# Forensic Report Model
# ---------------------------------------------------------------------------

class ForensicReport(BaseModel):
    """Structured forensic report (printable)."""
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
    # Removed: section_65b_certified (obsolete — was never a valid claim)
    integrity_record_type: str = "TAMPER_EVIDENT_TECHNICAL_INTEGRITY_RECORD"


# ---------------------------------------------------------------------------
# DB Preparation Models (1:1 mapping to future PostgreSQL tables)
# NOTE: These are Pydantic models only — NO persistence is wired in this
#       change set. They are preparation for a future migration.
# ---------------------------------------------------------------------------

class CaseDB(BaseModel):
    """Maps to: cases table"""
    case_id: str
    fir_number: str
    title: str
    police_station: str
    investigating_officer: str
    incident_date: str
    amount_inr: float
    chain: str
    suspect_wallet: str
    token: str
    notes: str
    created_at: Optional[str] = None


class WalletDB(BaseModel):
    """Maps to: wallets table"""
    address: str
    chain: str
    first_seen_case_id: Optional[str] = None
    risk_score: int = 0
    risk_level: str = "LOW"
    is_vasp_associated: bool = False
    vasp_id: Optional[str] = None


class TransactionDB(BaseModel):
    """Maps to: transactions table"""
    tx_id: str
    from_address: str
    to_address: str
    amount: float
    token: str
    timestamp_iso: Optional[str] = None
    block_number: Optional[int] = None
    is_synthetic: bool = False
    case_id: Optional[str] = None
    hop: int = 0


class VaspDB(BaseModel):
    """Maps to: vasps table"""
    vasp_id: str
    vasp_name: str
    country: str
    fiu_ind_registered: bool
    fiu_registration_number: Optional[str] = None
    compliance_nodal_email: str
    sahyog_integrated: bool = False


class VaspAddressDB(BaseModel):
    """Maps to: vasp_addresses table"""
    address: str
    vasp_id: str
    label_type: str   # hot_wallet, deposit_sweep, cold_storage
    chain: str
    strength: str     # verified, recognized, inferred, weak


class AttributionEvidenceDB(BaseModel):
    """Maps to: attribution_evidence table"""
    investigation_run_id: str
    case_id: str
    suspect_wallet: str
    attributed_vasp_id: Optional[str] = None
    confidence_score: float
    sha256_hash: str
    created_at: Optional[str] = None


class InvestigationRunDB(BaseModel):
    """Maps to: investigation_runs table"""
    run_id: str
    case_id: str
    suspect_wallet: str
    chain: str
    max_hops: int
    source_provider: str
    started_at: str
    completed_at: Optional[str] = None
    result_summary: Optional[str] = None
