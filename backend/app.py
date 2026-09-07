"""
Main FastAPI server for VASP TRACE: Automated VASP Attribution & Cross-Case Forensics Platform.
Integrates 8-pillar multi-chain ingestion, VASP intelligence, sanctions screening, and CCTNS database store.
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import hashlib
import sqlite3

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

# Database setup for cctns_forensics.db
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cctns_forensics.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_cctns_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # 1. CCTNS Cases Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cctns_cases (
                case_id TEXT PRIMARY KEY,
                fir_number TEXT,
                title TEXT,
                police_station TEXT,
                investigating_officer TEXT,
                incident_date TEXT,
                amount_inr REAL,
                chain TEXT,
                suspect_wallet TEXT,
                token TEXT,
                notes TEXT,
                status TEXT DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 2. Investigation Runs Table (VASPs identified & 72-hr asset holds)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investigation_runs (
                run_id TEXT PRIMARY KEY,
                case_id TEXT,
                attributed_vasp TEXT,
                confidence_score REAL,
                hold_active INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 3. Syndicate Shared Infrastructure Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS syndicate_registry (
                wallet_address TEXT,
                case_id TEXT,
                role TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (wallet_address, case_id)
            )
        """)

        # Seed initial cases if empty
        cursor.execute("SELECT COUNT(*) FROM cctns_cases")
        if cursor.fetchone()[0] == 0:
            initial_cases = [
                (
                    "CASE-147",
                    "FIR/2026/CY-HYD/304",
                    "₹1,80,000 Loan App Extortion Case",
                    "Cyber Crime Police Station, Cyberabad",
                    "Cyber Cell Officer",
                    "2026-08-30",
                    180000.0,
                    "TRON (TRC-20)",
                    "TJ9kLpBw81xPqrN4x78G44mX2e1Vb889Zq",
                    "USDT",
                    "Victim extorted via fake loan app. Stolen money converted to crypto USDT and moved across middleman wallets to an unknown exchange.",
                    "ACTIVE",
                    "2026-08-30 10:15:00"
                ),
                (
                    "CASE-101",
                    "FIR/2026/CY-MUM/892",
                    "₹50,000 Telegram Investment & Task Scam",
                    "Cyber Crime Police Station, BKC Mumbai",
                    "Cyber Cell Officer",
                    "2026-08-24",
                    50000.0,
                    "Ethereum (ERC-20)",
                    "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97",
                    "USDT",
                    "Victim defrauded by telegram work-from-home task scam. Funds routed to shared mule wallet.",
                    "ACTIVE",
                    "2026-08-24 14:30:00"
                ),
                (
                    "CASE-088",
                    "FIR/2026/CY-BLR/112",
                    "₹3,20,000 AI Trading Bot Scam",
                    "Cyber Crime Police Station, Bengaluru",
                    "Cyber Cell Officer",
                    "2026-08-15",
                    320000.0,
                    "Bitcoin (BTC)",
                    "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                    "BTC",
                    "Victim deposited into fraudulent AI automated crypto trading bot scheme.",
                    "ACTIVE",
                    "2026-08-15 09:45:00"
                )
            ]
            cursor.executemany("""
                INSERT INTO cctns_cases (case_id, fir_number, title, police_station, investigating_officer, incident_date, amount_inr, chain, suspect_wallet, token, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, initial_cases)

        # Seed investigation_runs if empty
        cursor.execute("SELECT COUNT(*) FROM investigation_runs")
        if cursor.fetchone()[0] == 0:
            initial_runs = [
                ("RUN-147-01", "CASE-147", "CoinDCX", 0.94, 1, "2026-08-30 11:00:00"),
                ("RUN-101-01", "CASE-101", "Binance", 0.88, 1, "2026-08-24 15:10:00"),
                ("RUN-088-01", "CASE-088", "CoinSwitch", 0.91, 1, "2026-08-15 10:20:00")
            ]
            cursor.executemany("""
                INSERT INTO investigation_runs (run_id, case_id, attributed_vasp, confidence_score, hold_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, initial_runs)

        # Seed syndicate_registry if empty
        cursor.execute("SELECT COUNT(*) FROM syndicate_registry")
        if cursor.fetchone()[0] == 0:
            initial_syndicates = [
                ("0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C", "CASE-101", "Shared Intermediary Mule", "2026-08-24 14:35:00"),
                ("0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C", "CASE-147", "Shared Intermediary Mule", "2026-08-30 10:20:00")
            ]
            cursor.executemany("""
                INSERT INTO syndicate_registry (wallet_address, case_id, role, first_seen)
                VALUES (?, ?, ?, ?)
            """, initial_syndicates)
        conn.commit()

init_cctns_db()

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

@app.get("/api/dashboard/my-cases")
def get_dashboard_cases():
    """
    Returns dynamic dashboard metrics and active cases from cctns_forensics.db.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Total count of rows in cctns_cases
        cursor.execute("SELECT COUNT(*) FROM cctns_cases WHERE status = 'ACTIVE' OR status IS NULL")
        active_cases_count = cursor.fetchone()[0]

        # 2. Count of unique attributed exchanges from investigation_runs
        cursor.execute("SELECT COUNT(DISTINCT attributed_vasp) FROM investigation_runs WHERE attributed_vasp IS NOT NULL AND attributed_vasp != ''")
        vasps_identified_count = cursor.fetchone()[0]

        # 3. Count of active 72-hour asset holds from investigation_runs
        cursor.execute("SELECT COUNT(*) FROM investigation_runs WHERE hold_active = 1")
        active_holds_count = cursor.fetchone()[0]

        # 4. Count from syndicate_registry
        cursor.execute("SELECT COUNT(*) FROM syndicate_registry")
        syndicates_linked_count = cursor.fetchone()[0]

        # Fetch all active cases ordered by created_at DESC
        cursor.execute("""
            SELECT case_id, fir_number, title, police_station, investigating_officer,
                   incident_date, amount_inr, chain, suspect_wallet, token, notes, status, created_at
            FROM cctns_cases
            WHERE status = 'ACTIVE' OR status IS NULL
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        cases_list = [dict(row) for row in rows]

    return {
        "metrics": {
            "active_cases": active_cases_count,
            "vasps_identified": vasps_identified_count,
            "active_holds": active_holds_count,
            "syndicates_linked": syndicates_linked_count
        },
        "cases": cases_list
    }

@app.post("/api/cases/create")
def create_case(payload: Dict[str, Any] = Body(...)):
    """
    Creates a new case record in cctns_forensics.db and registers it in the live analysis engine.
    """
    fir_number = payload.get("fir_number", "").strip() or "FIR/2026/CY-GEN/001"
    suspect_wallet = payload.get("suspect_wallet", "").strip()
    chain = payload.get("chain", "TRON")
    amount_inr = float(payload.get("amount_inr", 180000))
    notes = payload.get("notes", "New cybercrime investigation docket.")
    title = payload.get("title", "").strip() or f"₹{int(amount_inr):,} Crypto Fraud Investigation"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cctns_cases")
        count = cursor.fetchone()[0]
        case_id = f"CASE-{count + 148}"

        cursor.execute("""
            INSERT INTO cctns_cases (case_id, fir_number, title, police_station, investigating_officer, incident_date, amount_inr, chain, suspect_wallet, token, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            case_id,
            fir_number,
            title,
            "Cyber Crime Police Station",
            "Investigating Officer",
            datetime.now().strftime("%Y-%m-%d"),
            amount_inr,
            chain,
            suspect_wallet,
            "USDT",
            notes,
            "ACTIVE"
        ))
        conn.commit()

    # Register in CASES_DATABASE so immediate workbench analysis works
    new_case_obj = generate_custom_trace(suspect_wallet, chain=chain)
    new_case_obj["case_id"] = case_id
    new_case_obj["title"] = title
    new_case_obj["fir_number"] = fir_number
    new_case_obj["amount_inr"] = amount_inr
    new_case_obj["chain"] = chain
    new_case_obj["notes"] = notes
    CASES_DATABASE[case_id] = new_case_obj
    cross_case_engine.register_case_nodes(case_id, new_case_obj, new_case_obj["nodes"])

    return {
        "status": "SUCCESS",
        "case_id": case_id,
        "case": {
            "case_id": case_id,
            "fir_number": fir_number,
            "title": title,
            "amount_inr": amount_inr,
            "chain": chain,
            "suspect_wallet": suspect_wallet,
            "notes": notes
        }
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
    if case_key in CASES_DATABASE:
        return CASES_DATABASE[case_key]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cctns_cases WHERE UPPER(case_id) = ?", (case_key,))
        row = cursor.fetchone()
        if row:
            case_dict = dict(row)
            generated = generate_custom_trace(case_dict["suspect_wallet"], chain=case_dict.get("chain", "TRON"))
            generated["case_id"] = case_dict["case_id"]
            generated["title"] = case_dict["title"]
            generated["fir_number"] = case_dict["fir_number"]
            generated["police_station"] = case_dict.get("police_station", "Cyber Crime Unit")
            generated["amount_inr"] = case_dict["amount_inr"]
            generated["chain"] = case_dict["chain"]
            generated["notes"] = case_dict["notes"]
            CASES_DATABASE[case_key] = generated
            return generated

    raise HTTPException(status_code=404, detail="Case ID not found")

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
