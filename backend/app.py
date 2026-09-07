"""
Main FastAPI server for VA-TRACE: Automated VASP Attribution & Cross-Case Intelligence System.
"""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import sqlite3

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
    return {"status": "ACTIVE", "system": "VA-TRACE Core Engine", "version": "1.0.0"}

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
