"""
Main FastAPI server for VA-TRACE: Automated VASP Attribution & Cross-Case Intelligence System.
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

app = FastAPI(
    title="VASP TRACE: VASP Attribution & Cross-Case Forensics Engine",
    description="Automated Attribution of Unknown Cryptocurrency Wallets to Nearest VASPs through Blockchain Intelligence",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate Core Forensic Engines
graph_engine = GraphEngine()
attribution_engine = AttributionEngine()
cross_case_engine = CrossCaseEngine()
sahyog_router = SahyogRouter()
evidence_verifier = EvidenceVerifier()

# Register initial cases into the persistent cross-case engine
for c_id, c_data in CASES_DATABASE.items():
    cross_case_engine.register_case_nodes(c_id, c_data, c_data["nodes"])

@app.get("/api/health")
def health_check():
    return {"status": "ACTIVE", "system": "VA-TRACE Core Engine", "version": "1.0.0"}

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
            "incident_date": c["incident_date"]
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
    Main pipeline:
    1. Retrieves/generates multi-hop transaction graph
    2. Builds NetworkX directed graph & analyzes fund flow
    3. Calculates Explainable VASP Attribution & Candidate Ranking
    4. Evaluates Cross-Case Syndicate Intelligence
    5. Generates SAHYOG Lawful Requisition Draft
    6. Produces SHA-256 Forensic Hash Seal
    """
    case_id = payload.get("case_id", "").upper()
    wallet_address = payload.get("wallet_address", "").strip()
    chain = payload.get("chain", "Ethereum")
    max_hops = int(payload.get("max_hops", 4))

    # Determine case data source
    if case_id in CASES_DATABASE and (not wallet_address or wallet_address == CASES_DATABASE[case_id]["suspect_wallet"]):
        case_data = CASES_DATABASE[case_id]
    elif wallet_address:
        case_data = generate_custom_trace(wallet_address, chain=chain, max_hops=max_hops)
    else:
        case_data = CASES_DATABASE["CASE-101"]

    # 1. Graph Engine Traversal
    G = graph_engine.build_graph(case_data["nodes"], case_data["edges"])
    flow_analysis = graph_engine.analyze_fund_flow(G, case_data["suspect_wallet"])
    anomalies = graph_engine.detect_mixers_and_bridges(G)

    # 2. Explainable VASP Attribution Engine
    attribution = attribution_engine.compute_attribution(case_data, flow_analysis)

    # 3. Cross-Case Intelligence Engine
    cross_case = cross_case_engine.check_cross_case_links(case_data["case_id"], case_data["nodes"])

    # 4. SAHYOG Legal Requisition Generator
    sahyog_req = sahyog_router.generate_lawful_request(case_data, attribution)

    # 5. Evidence Verifier & SHA-256 Hash
    forensic_seal = evidence_verifier.generate_forensic_hash(case_data, attribution.model_dump())

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
            "notes": case_data["notes"]
        },
        "graph": {
            "nodes": case_data["nodes"],
            "edges": case_data["edges"]
        },
        "flow_analysis": flow_analysis,
        "attribution": attribution,
        "cross_case_alert": cross_case,
        "sahyog_request": sahyog_req,
        "evidence_seal": forensic_seal,
        "anomalies": anomalies
    }

@app.post("/api/sahyog/dispatch")
def dispatch_sahyog(payload: Dict[str, Any] = Body(...)):
    """Simulates dispatch of a Section 91/102 legal notice to VASP Compliance Nodal Desk."""
    return sahyog_router.dispatch_sahyog_request(payload)

@app.post("/api/evidence/verify")
def verify_evidence_hash(payload: Dict[str, Any] = Body(...)):
    """Validates user-submitted SHA-256 hash against expected blockchain forensic snapshot."""
    submitted = payload.get("submitted_hash", "")
    expected = payload.get("expected_hash", "")
    return evidence_verifier.verify_hash(submitted, expected)

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

    @app.get("/")
    def serve_ui():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
