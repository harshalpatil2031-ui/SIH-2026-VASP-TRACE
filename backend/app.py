"""
Main FastAPI server for VASP TRACE: Automated VASP Attribution & Cross-Case Forensics Platform.
Integrates 8-pillar multi-chain ingestion, VASP intelligence, sanctions screening, and CCTNS database store.
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional
import os
import hashlib
from datetime import datetime

try:
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
    from .data_sources import CCTNSDatabaseStore, BlockchainIngestionAdapter
except (ImportError, ValueError):
    from models import (
        NodeData, EdgeData, GraphPayload, AttributionResult,
        CrossCaseAlert, SahyogRequest, ForensicReport
    )
    from mock_blockchain import CASES_DATABASE, KNOWN_VASPS, generate_custom_trace
    from graph_engine import GraphEngine
    from attribution_engine import AttributionEngine
    from cross_case_engine import CrossCaseEngine
    from sahyog_router import SahyogRouter
    from evidence_verifier import EvidenceVerifier
    from data_sources import CCTNSDatabaseStore, BlockchainIngestionAdapter

app = FastAPI(
    title="VASP TRACE: VASP Attribution & Cross-Case Forensics Engine",
    description="Automated Attribution of Unknown Cryptocurrency Wallets to Nearest VASPs through Multi-Chain Graph Intelligence",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate Core Forensic Engines & PostgreSQL/CCTNS Store
graph_engine = GraphEngine()
attribution_engine = AttributionEngine()
cross_case_engine = CrossCaseEngine()
sahyog_router = SahyogRouter()
evidence_verifier = EvidenceVerifier()
db_store = CCTNSDatabaseStore()
ingestion_adapter = BlockchainIngestionAdapter()

# Register initial cases into the persistent cross-case engine and database
for c_id, c_data in CASES_DATABASE.items():
    cross_case_engine.register_case_nodes(c_id, c_data, c_data["nodes"])
    db_store.save_case(c_data)

@app.get("/api/health")
def health_check():
    return {
        "status": "ACTIVE",
        "system": "VASP TRACE Core Forensics Engine (v2.0)",
        "version": "2.0.0",
        "mode": "OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER",
        "database": db_store.get_db_status()["source_8_database"]["engine"],
        "compliance": "BNSS 2023 / BSA 2023 / PMLA 2002 / FATF Recommendation 15 & 16"
    }

@app.get("/api/cases")
def list_cases():
    """Returns a list of all active cybercrime cases from the CCTNS store."""
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
            "token": c.get("token", "USDT")
        })
    return summary

@app.post("/api/cases/create")
def create_case(payload: Dict[str, Any] = Body(...)):
    """Dynamically creates and stores a new FIR case docket in the CCTNS database."""
    fir_num = payload.get("fir_number", f"FIR/2026/CY/{len(CASES_DATABASE)+100}")
    wallet = payload.get("suspect_wallet", "").strip()
    chain = payload.get("chain", "TRON")
    amount = float(payload.get("amount_inr", 150000))
    notes = payload.get("notes", "New cyber extortion complaint.")

    # 🛡️ Validate Cryptographic Wallet Address Format
    val_res = ingestion_adapter.validate_wallet_address(wallet, chain)
    if not val_res["is_valid"]:
        raise HTTPException(status_code=400, detail=val_res["message"])
    
    case_id = f"CASE-{hashlib.md5(fir_num.encode()).hexdigest()[:3].upper()}{len(CASES_DATABASE)+1}"
    
    new_trace = generate_custom_trace(wallet, chain=chain, max_hops=4)
    new_trace["case_id"] = case_id
    new_trace["title"] = f"₹{amount:,.0f} {chain} Fraud Case"
    new_trace["fir_number"] = fir_num
    new_trace["police_station"] = payload.get("police_station", "Cyber Crime Unit, Hyderabad")
    new_trace["amount_inr"] = amount
    new_trace["notes"] = notes
    
    CASES_DATABASE[case_id] = new_trace
    cross_case_engine.register_case_nodes(case_id, new_trace, new_trace["nodes"])
    db_store.save_case(new_trace)
    
    return {"status": "SUCCESS", "case_id": case_id, "case": new_trace}

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
    Main Multi-Stage Forensic Intelligence Pipeline (v2.0):
    1. Validates wallet address structure
    2. BFS multi-hop graph traversal with cycle prevention & hop bounds
    3. Entity Intelligence lookup & 6-factor dynamic VASP attribution (zero case-ID logic)
    4. Evaluates Cross-Case Infrastructure Correlation
    5. Generates BNSS 2023 SAHYOG Notice & Section 63 BSA SHA-256 seal
    6. Returns SuggestedLawfulAction draft object
    """
    case_id = payload.get("case_id", "").upper()
    wallet_address = payload.get("wallet_address", "").strip()
    chain = payload.get("chain", "TRON")
    max_hops = int(payload.get("max_hops", 4))

    # Validate Cryptographic Wallet Address Format if custom address provided
    if wallet_address and case_id not in CASES_DATABASE:
        val_res = ingestion_adapter.validate_wallet_address(wallet_address, chain)
        if not val_res["is_valid"]:
            raise HTTPException(status_code=400, detail=val_res["message"])

    # Determine case data source
    if case_id in CASES_DATABASE and (not wallet_address or wallet_address == CASES_DATABASE[case_id]["suspect_wallet"]):
        case_data = CASES_DATABASE[case_id]
    elif wallet_address:
        val_res = ingestion_adapter.validate_wallet_address(wallet_address, chain)
        if not val_res["is_valid"]:
            raise HTTPException(status_code=400, detail=val_res["message"])
        case_data = generate_custom_trace(wallet_address, chain=chain, max_hops=max_hops)
    else:
        case_data = CASES_DATABASE["CASE-147"]

    # 1. BFS Graph Engine Traversal
    G = graph_engine.build_graph(case_data["nodes"], case_data["edges"])
    flow_analysis = graph_engine.analyze_fund_flow(G, case_data["suspect_wallet"], max_depth=max_hops)
    anomalies = graph_engine.detect_mixers_and_bridges(G)

    # 2. Dynamic 6-Factor VASP Attribution Engine
    attribution = attribution_engine.compute_attribution(case_data, flow_analysis)

    # 3. Cross-Case Infrastructure Intelligence Engine
    cross_case = cross_case_engine.check_cross_case_links(case_data["case_id"], case_data["nodes"])

    # 4. SAHYOG BNSS 2023 Legal Notice Generator
    sahyog_req = sahyog_router.generate_lawful_request(case_data, attribution)
    suggested_action = sahyog_router.generate_suggested_lawful_action(case_data, attribution)

    # 5. Section 63 BSA Digital Evidence Verifier & SHA-256 Seal
    forensic_seal = evidence_verifier.generate_forensic_hash(case_data, attribution.model_dump())

    # 6. Persist to CCTNS Database Store
    db_store.save_case(case_data)

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
            "token": case_data.get("token", "USDT"),
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
        "suggested_lawful_action": suggested_action,
        "evidence_seal": forensic_seal,
        "anomalies": anomalies,
        "intelligence_sources": attribution.intelligence_sources
    }

@app.post("/api/sahyog/dispatch")
def dispatch_sahyog(payload: Dict[str, Any] = Body(...)):
    """Dispatches a Section 94/106 BNSS 2023 notice to the exchange Nodal Desk via SAHYOG."""
    return sahyog_router.dispatch_sahyog_request(payload)

@app.post("/api/evidence/verify")
def verify_evidence_hash(payload: Dict[str, Any] = Body(...)):
    """Validates Section 63 BSA SHA-256 digital evidence seal against courtroom standard."""
    submitted_hash = payload.get("submitted_hash", "")
    expected_hash = payload.get("expected_hash", "")
    return evidence_verifier.verify_hash(submitted_hash, expected_hash)

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

    @app.get("/")
    def serve_ui():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
