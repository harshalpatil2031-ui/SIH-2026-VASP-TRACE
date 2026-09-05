from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

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
    confidence_score: float
    confidence_level: str  # HIGH, MEDIUM, LOW
    explainability: List[ExplainabilityFactor]
    total_hops: int
    total_volume_tracked: float
    volume_to_vasp: float
    flow_percentage: float
    time_to_deposit_minutes: int
    sweep_detected: bool

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
    legal_section: str  # Section 91 CrPC / Section 102 CrPC / PMLA 2002
    urgency: str  # IMMEDIATE, HIGH, STANDARD
    fiu_nodal_officer: str
    crypto_amount: str
    inr_equivalent: str
    status: str  # DRAFT, DISPATCHED, ACKNOWLEDGED, ASSETS_FROZEN
    timestamp: str
    dispatch_receipt_hash: Optional[str] = None

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
    section_65b_certified: bool = True
