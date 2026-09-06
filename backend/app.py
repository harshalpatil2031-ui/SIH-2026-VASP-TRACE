"""
Main FastAPI server for VASP TRACE: Automated VASP Attribution & Cross-Case
Infrastructure Correlation System.

OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER.
This prototype uses pre-seeded synthetic data.  No live blockchain data is
accessed.  All transaction IDs are SIM- prefixed to make this unambiguous.
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional
import os

from .models import (
    NodeData, EdgeData, GraphPayload, AttributionResult,
    CrossCaseAlert, SahyogRequest, ForensicReport
)
from .mock_blockchain import CASES_DATABASE, KNOWN_VASPS, generate_custom_trace
from .graph_engine import GraphEngine
from .attribution_engine import AttributionEngine
from .cross_case_engine import CrossCaseEngine
from .sahyog_router import SahyogRouter
from .evidence_verifier import EvidenceVerifier
from .entity_intelligence import EntityIntelligence

app = FastAPI(
    title="VASP TRACE: VASP Attribution & Cross-Case Infrastructure Correlation Engine",
    description=(
        "Automated Attribution of Unknown Cryptocurrency Wallets to Nearest "
        "Virtual Asset Service Providers (VASPs) through Blockchain Intelligence. "
        "OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER. "
        "No live blockchain connectivity in this prototype."
    ),
    version="2.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate Core Forensic Engines (shared entity intelligence layer)
entity_intel = EntityIntelligence()
graph_engine = GraphEngine()
attribution_engine = AttributionEngine(entity_intel=entity_intel)
cross_case_engine = CrossCaseEngine()
sahyog_router = SahyogRouter()
evidence_verifier = EvidenceVerifier()

# Register initial cases into the persistent cross-case engine
for c_id, c_data in CASES_DATABASE.items():
    cross_case_engine.register_case_nodes(c_id, c_data, c_data["nodes"])


@app.get("/api/health")
def health_check():
    return {
        "status": "ACTIVE",
        "system": "VASP TRACE Core Engine",
        "version": "2.0.0",
        "mode": "OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER",
    }


@app.get("/api/cases")
def list_cases():
    """Returns a list of preloaded cybercrime cases with summary metadata."""
    summary = []
    for c_id, c in CASES_DATABASE.items():
        summary.append({
            "case_id": c["case_id"],
            "title": c["title"],
            "fir_number": c["fir_number"],
            "police_station": c["police_station"],
            "amount_inr": c["amount_inr"],
            "chain": c["chain"],
            "suspect_wallet": c["suspect_wallet"],
            "incident_date": c["incident_date"],
        })
    return summary


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    """Retrieves full investigation case details."""
    case_key = case_id.upper()
    if case_key not in CASES_DATABASE:
        raise HTTPException(status_code=404, detail="Case ID not found")
    return CASES_DATABASE[case_key]


@app.post("/api/trace")
def trace_and_attribute(payload: Dict[str, Any] = Body(...)):
    """
    Main forensic pipeline:
    1. Retrieve/generate multi-hop transaction graph (synthetic data)
    2. Build NetworkX directed graph & analyze fund flow via BFS
    3. Run Explainable VASP Attribution (4-stage pipeline, no case-ID logic)
    4. Evaluate Cross-Case Infrastructure Correlation
    5. Generate SAHYOG Lawful Requisition Draft (BNSS 2023)
    6. Produce SHA-256 Tamper-Evident Technical Integrity Record

    OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER.
    All transaction data is synthetic. No live blockchain is accessed.
    """
    case_id = payload.get("case_id", "").upper()
    wallet_address = payload.get("wallet_address", "").strip()
    chain = payload.get("chain", "Ethereum")
    max_hops = int(payload.get("max_hops", 4))

    # Determine case data source
    if case_id in CASES_DATABASE and (
        not wallet_address or
        wallet_address == CASES_DATABASE[case_id]["suspect_wallet"]
    ):
        case_data = CASES_DATABASE[case_id]
    elif wallet_address:
        case_data = generate_custom_trace(
            wallet_address, chain=chain, max_hops=max_hops
        )
    else:
        case_data = CASES_DATABASE["CASE-101"]

    # 1. Graph Engine Traversal (BFS, VASP-agnostic)
    G = graph_engine.build_graph(case_data["nodes"], case_data["edges"])
    flow_analysis = graph_engine.analyze_fund_flow(
        G, case_data["suspect_wallet"], max_hops=max_hops
    )
    anomalies = graph_engine.detect_mixers_and_bridges(G)

    # 2. Explainable VASP Attribution (4-stage, no case-ID logic)
    attribution = attribution_engine.compute_attribution(case_data, flow_analysis)

    # 3. Cross-Case Infrastructure Correlation
    cross_case = cross_case_engine.check_cross_case_links(
        case_data["case_id"], case_data["nodes"]
    )

    # 4. SAHYOG Lawful Requisition Draft (BNSS 2023)
    sahyog_req = sahyog_router.generate_lawful_request(case_data, attribution)

    # 5. SHA-256 Tamper-Evident Technical Integrity Record
    attr_dict = attribution.model_dump()
    forensic_seal = evidence_verifier.generate_forensic_hash(
        case_data,
        attr_dict,
        investigation_run_id=attribution.investigation_run_id,
    )

    # Bound the graph visualization to max_hops
    valid_tx_hashes = {hr["tx_hash"] for hr in flow_analysis.get("hop_records", [])}
    filtered_edges = [e for e in case_data.get("edges", []) if e.get("tx_hash") in valid_tx_hashes]
    valid_node_ids = {case_data.get("suspect_wallet", "")}
    for e in filtered_edges:
        valid_node_ids.add(e["source"])
        valid_node_ids.add(e["target"])
    filtered_nodes = [n for n in case_data.get("nodes", []) if n["id"] in valid_node_ids]

    return {
        "case_metadata": {
            "case_id": case_data["case_id"],
            "title": case_data["title"],
            "fir_number": case_data["fir_number"],
            "police_station": case_data["police_station"],
            "investigating_officer": case_data["investigating_officer"],
            "incident_date": case_data["incident_date"],
            "amount_inr": case_data["amount_inr"],
            "chain": case_data["chain"],
            "suspect_wallet": case_data["suspect_wallet"],
            "token": case_data["token"],
            "notes": case_data["notes"],
        },
        "graph": {
            "nodes": filtered_nodes,
            "edges": filtered_edges,
        },
        "flow_analysis": flow_analysis,
        "attribution": attribution,
        "cross_case_alert": cross_case,
        "sahyog_request": sahyog_req,
        "evidence_seal": forensic_seal,
        "anomalies": anomalies,
    }


@app.post("/api/sahyog/dispatch")
def dispatch_sahyog(payload: Dict[str, Any] = Body(...)):
    """
    Simulates submission of a BNSS 2023 lawful requisition DRAFT to the
    SAHYOG Compliance Portal for authorized investigator review.

    IMPORTANT: This is a SIMULATION. No account freeze or legal action is
    automatically triggered. All actions require authorized investigator approval.
    """
    return sahyog_router.dispatch_sahyog_request(payload)


@app.post("/api/evidence/verify")
def verify_evidence_hash(payload: Dict[str, Any] = Body(...)):
    """
    Validates a submitted SHA-256 hash against the expected tamper-evident
    technical integrity record hash.
    """
    submitted = payload.get("submitted_hash", "")
    expected = payload.get("expected_hash", "")
    return evidence_verifier.verify_hash(submitted, expected)


# Mount frontend static files
frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"
)
if os.path.exists(frontend_dir):
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(frontend_dir, "static")),
        name="static",
    )

    @app.get("/")
    def serve_ui():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
