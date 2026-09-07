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
import json
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
    from .settings import settings
    from .trace_coordinator import TraceCoordinator
    from .live_trace_jobs import LiveTraceJobManager
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
    from settings import settings
    from trace_coordinator import TraceCoordinator
    from live_trace_jobs import LiveTraceJobManager

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

# One canonical database location.  The dashboard and forensic store must never
# depend on the process working directory, otherwise they can read different files.
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cctns_forensics.db")

# Instantiate Core Forensic Engines & PostgreSQL/CCTNS Store
graph_engine = GraphEngine()
attribution_engine = AttributionEngine()
cross_case_engine = CrossCaseEngine()
sahyog_router = SahyogRouter()
evidence_verifier = EvidenceVerifier()
db_store = CCTNSDatabaseStore(DB_PATH)
ingestion_adapter = BlockchainIngestionAdapter()
trace_coordinator = TraceCoordinator()
live_trace_jobs = LiveTraceJobManager()

# Register initial cases into the persistent cross-case engine and database
for c_id, c_data in CASES_DATABASE.items():
    cross_case_engine.register_case_nodes(c_id, c_data, c_data["nodes"])
    db_store.save_case(c_data)

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
        # Ensure schema compatibility with preexisting database
        case_cols = {row[1] for row in cursor.execute("PRAGMA table_info(cctns_cases)").fetchall()}
        for col, col_type in [("title", "TEXT"), ("amount_inr", "REAL"), ("token", "TEXT DEFAULT 'USDT'"), ("notes", "TEXT"), ("incident_date", "TEXT")]:
            if col not in case_cols:
                cursor.execute(f"ALTER TABLE cctns_cases ADD COLUMN {col} {col_type}")

        run_cols = {row[1] for row in cursor.execute("PRAGMA table_info(investigation_runs)").fetchall()}
        for col, col_type in [("attributed_vasp", "TEXT"), ("confidence_score", "REAL DEFAULT 0.0"), ("hold_active", "INTEGER DEFAULT 0")]:
            if col not in run_cols:
                cursor.execute(f"ALTER TABLE investigation_runs ADD COLUMN {col} {col_type}")
        # Older trace rows predate the dispatch workflow.  They cannot represent
        # an acknowledged exchange hold when no target VASP was recorded.
        cursor.execute("""
            UPDATE investigation_runs
            SET hold_active = 0
            WHERE attributed_vasp IS NULL OR TRIM(attributed_vasp) = ''
        """)
        # Backfill dashboard fields from immutable historic trace evidence that
        # was saved before these reporting columns were introduced.
        legacy_runs = cursor.execute("""
            SELECT run_id, attribution_json FROM investigation_runs
            WHERE attributed_vasp IS NULL OR TRIM(attributed_vasp) = ''
        """).fetchall()
        for run_id, attribution_json in legacy_runs:
            try:
                attribution_data = json.loads(attribution_json or "{}")
                vasp_name = attribution_data.get("primary_vasp", {}).get("vasp_name")
                confidence = float(attribution_data.get("confidence_score", 0))
                if vasp_name and vasp_name != "No qualifying VASP endpoint found within max_hops":
                    cursor.execute(
                        "UPDATE investigation_runs SET attributed_vasp = ?, confidence_score = ? WHERE run_id = ?",
                        (vasp_name, confidence, run_id),
                    )
            except (TypeError, ValueError, json.JSONDecodeError):
                continue

        synd_cols = {row[1] for row in cursor.execute("PRAGMA table_info(syndicate_registry)").fetchall()}
        for col, col_type in [("case_id", "TEXT"), ("role", "TEXT DEFAULT 'Shared Intermediary Mule'"), ("first_seen", "TEXT")]:
            if col not in synd_cols:
                cursor.execute(f"ALTER TABLE syndicate_registry ADD COLUMN {col} {col_type}")

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
                INSERT OR REPLACE INTO cctns_cases (case_id, fir_number, title, police_station, investigating_officer, incident_date, amount_inr, stolen_amount_inr, chain, suspect_wallet, token, notes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[6], c[7], c[8], c[9], c[10], c[11], c[12])
                for c in initial_cases
            ])

        # Seed investigation_runs if empty
        cursor.execute("SELECT COUNT(*) FROM investigation_runs")
        if cursor.fetchone()[0] == 0:
            initial_runs = [
                ("RUN-147-01", "CASE-147", "DEMO", "TRON", "TJ9kLpBw81xPqrN4x78G44mX2e1Vb889Zq", "hash147", "{}", "{}", "2026-08-30 11:00:00", "{}", "CoinDCX", 0.94, 1),
                ("RUN-101-01", "CASE-101", "DEMO", "Ethereum", "0x4838B106FCe9647Bdf1E7877BF73cE8B0BAD5f97", "hash101", "{}", "{}", "2026-08-24 15:10:00", "{}", "Binance", 0.88, 1),
                ("RUN-088-01", "CASE-088", "DEMO", "Bitcoin", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "hash088", "{}", "{}", "2026-08-15 10:20:00", "{}", "CoinSwitch", 0.91, 1)
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO investigation_runs (run_id, case_id, data_mode, chain, suspect_wallet, manifest_hash, provenance_json, attribution_json, created_at, manifest_json, attributed_vasp, confidence_score, hold_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, initial_runs)

        # Seed syndicate_registry if empty
        cursor.execute("SELECT COUNT(*) FROM syndicate_registry")
        if cursor.fetchone()[0] == 0:
            initial_syndicates = [
                ("0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C", "CASE-101", "Shared Intermediary Mule", "2026-08-24 14:35:00", "FIR/2026/CY-MUM/892, FIR/2026/CY-HYD/304", 2.4, "2026-08-24"),
                ("0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C", "CASE-147", "Shared Intermediary Mule", "2026-08-30 10:20:00", "FIR/2026/CY-MUM/892, FIR/2026/CY-HYD/304", 2.4, "2026-08-30")
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO syndicate_registry (wallet_address, case_id, role, first_seen, linked_fir_numbers, risk_multiplier, first_seen_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
        "trace_mode": settings.default_mode,
        "live_sources_configured": settings.live_sources_configured,
        "database": db_store.get_db_status()["source_8_database"]["engine"],
        "compliance": "BNSS 2023 / BSA 2023 / PMLA 2002 / FATF Recommendation 15 & 16"
    }

@app.get("/api/sources/status")
def source_status():
    """Reports configuration availability without ever exposing credentials."""
    return {
        "default_trace_mode": settings.default_mode,
        "sources": {
            "etherscan": {"configured": settings.live_sources_configured["etherscan"], "chain": "Ethereum"},
            "trongrid": {"configured": settings.live_sources_configured["trongrid"], "chain": "TRON"},
            "bitquery": {"configured": settings.live_sources_configured["bitquery"], "chain": "Multi-chain"},
            "synthetic_demo": {"configured": True, "chain": "Offline demonstration"},
        },
        "disclaimer": "Configuration availability is not evidence of a successful live retrieval. Each trace records its actual source.",
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
                   incident_date, COALESCE(amount_inr, stolen_amount_inr, 0) AS amount_inr,
                   chain, suspect_wallet, token, notes, status, created_at
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
    requested_mode = payload.get("trace_mode", settings.default_mode).upper()
    if requested_mode not in {"DEMO", "LIVE", "AUTO"}:
        raise HTTPException(status_code=400, detail="trace_mode must be DEMO, LIVE, or AUTO.")

    # Validate Cryptographic Wallet Address Format if custom address provided
    if wallet_address and case_id not in CASES_DATABASE:
        val_res = ingestion_adapter.validate_wallet_address(wallet_address, chain)
        if not val_res["is_valid"]:
            raise HTTPException(status_code=400, detail=val_res["message"])

    # Determine case data source
    live_requested = requested_mode in {"LIVE", "AUTO"} and bool(wallet_address)
    trace_provenance = {"data_mode": "DEMO", "source_events": []}
    if live_requested and wallet_address:
        try:
            live_graph = trace_coordinator.trace_live(wallet_address, chain, max_hops)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        case_data = {
            "case_id": case_id or "LIVE-%s" % wallet_address[-6:].upper(), "title": "Live Wallet Investigation",
            "fir_number": payload.get("fir_number", "UNASSIGNED"), "police_station": payload.get("police_station", "Unassigned"),
            "investigating_officer": "Authorized Investigator", "incident_date": datetime.utcnow().date().isoformat(),
            "amount_inr": float(payload.get("amount_inr", 0)), "chain": chain, "suspect_wallet": live_graph["root_address"],
            "token": "USDT", "notes": "Live, read-only on-chain trace. Attribution requires review.",
            "nodes": live_graph["nodes"], "edges": live_graph["edges"]}
        trace_provenance = live_graph
    elif case_id in CASES_DATABASE and (not wallet_address or wallet_address == CASES_DATABASE[case_id]["suspect_wallet"]):
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
    # Register suspect/mule wallets from this trace into the national syndicate index.
    # Guard: only persist when a real FIR number is present — unregistered live probes
    # must not pollute the national intelligence graph automatically.
    if case_data.get("fir_number", "UNASSIGNED") not in {"UNASSIGNED", "", None}:
        cross_case_engine.register_case_nodes(case_data["case_id"], case_data, case_data["nodes"])

    # 4. SAHYOG BNSS 2023 Legal Notice Generator
    sahyog_req = sahyog_router.generate_lawful_request(case_data, attribution)
    suggested_action = sahyog_router.generate_suggested_lawful_action(case_data, attribution)

    # 5. Section 63 BSA Digital Evidence Verifier & SHA-256 Seal
    forensic_seal = evidence_verifier.generate_forensic_hash(case_data, attribution.model_dump())
    trace_manifest = evidence_verifier.generate_trace_manifest(case_data, trace_provenance, attribution.model_dump())

    # 6. Persist to CCTNS Database Store
    db_store.save_case(case_data)
    db_store.save_trace_run(trace_manifest, case_data, trace_provenance, attribution.model_dump())
    sahyog_req.investigation_run_id = trace_manifest["investigation_run_id"]

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
        "action_eligibility": {
            "status": "VERIFIED_VASP_REACHED — REVIEW REQUIRED" if sahyog_req.eligible_for_dispatch else "UNRESOLVED — DEEP TRACE REQUIRED",
            "eligible_for_dispatch": sahyog_req.eligible_for_dispatch,
            "reason": sahyog_req.eligibility_reason,
            "examined_hop_scope": max_hops,
            "minimum_confidence": 75.0,
        },
        "evidence_seal": forensic_seal,
        "trace_manifest": trace_manifest,
        "anomalies": anomalies,
        "intelligence_sources": attribution.intelligence_sources
        ,"trace_provenance": trace_provenance
    }


@app.post("/api/trace/jobs")
def start_live_trace_job(payload: Dict[str, Any] = Body(...)):
    """Start a live investigation without holding the browser HTTP request open."""
    requested_mode = payload.get("trace_mode", settings.default_mode).upper()
    wallet_address = payload.get("wallet_address", "").strip()
    if requested_mode not in {"LIVE", "AUTO"} or not wallet_address:
        raise HTTPException(status_code=400, detail="Background trace jobs require a wallet and LIVE or AUTO mode.")
    return live_trace_jobs.submit(lambda: trace_and_attribute(payload))


@app.get("/api/trace/jobs/{job_id}")
def get_live_trace_job(job_id: str):
    job = live_trace_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Live trace job not found.")
    return job

@app.post("/api/sahyog/dispatch")
def dispatch_sahyog(payload: Dict[str, Any] = Body(...)):
    """Dispatches a Section 94/106 BNSS 2023 notice to the exchange Nodal Desk via SAHYOG."""
    try:
        run_id = payload.get("investigation_run_id", "")
        run = db_store.get_trace_run(run_id) if run_id else None
        if not run:
            raise ValueError("Dispatch blocked: a saved investigation run is required.")
        stored = run.get("attribution", {})
        stored_candidate = stored.get("primary_vasp", {})
        if (
            float(stored.get("confidence_score", 0)) < 75.0
            or stored_candidate.get("matched_cluster_id") in {None, "NONE"}
            or payload.get("target_wallet") != stored_candidate.get("deposit_address")
            or payload.get("vasp_name") != stored_candidate.get("vasp_name")
        ):
            raise ValueError("Dispatch blocked: the saved evidence run does not support this VASP request.")
        receipt = sahyog_router.dispatch_sahyog_request(payload)
        # The dashboard reports actual acknowledged holds, not every trace run.
        if receipt.get("status") == "DISPATCHED_AND_ACKNOWLEDGED":
            with get_db() as conn:
                conn.execute("UPDATE investigation_runs SET hold_active = 1 WHERE run_id = ?", (run_id,))
                conn.commit()
        return receipt
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@app.post("/api/evidence/verify")
def verify_evidence_hash(payload: Dict[str, Any] = Body(...)):
    """Validates Section 63 BSA SHA-256 digital evidence seal against courtroom standard."""
    submitted_hash = payload.get("submitted_hash", "")
    expected_hash = payload.get("expected_hash", "")
    return evidence_verifier.verify_hash(submitted_hash, expected_hash)

@app.get("/api/evidence/runs/{run_id}")
def get_evidence_run(run_id: str):
    """Read a saved evidence run without modifying it."""
    run = db_store.get_trace_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
    return run

@app.post("/api/evidence/runs/{run_id}/verify")
def verify_evidence_run(run_id: str):
    """Recompute the saved canonical manifest and compare it with its stored hash."""
    run = db_store.get_trace_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
    result = evidence_verifier.verify_trace_manifest(run["manifest_payload"], run["manifest_hash"])
    result.update({"run_id": run_id, "data_mode": run["data_mode"], "transaction_count": len(run["transactions"])})
    return result

@app.get("/api/evidence/runs/{run_id}/export")
def export_evidence_run(run_id: str):
    """Export a self-describing JSON evidence package for authorized review."""
    run = db_store.get_trace_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")
    return {"package_type": "VASP_TRACE_EVIDENCE_PACKAGE", "version": "1.0", "exported_at": datetime.utcnow().isoformat() + "Z",
            "disclaimer": "Technical evidence package. It requires authorized handling, investigator attestation, and applicable legal process.", "run": run}

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

    @app.get("/")
    def serve_ui():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
