# 🛡️ VASP TRACE: Automated Cryptocurrency Wallet Attribution & Cross-Case Infrastructure Correlation Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![NetworkX](https://img.shields.io/badge/Graph_Engine-NetworkX-orange)](https://networkx.org/)
[![Cytoscape.js](https://img.shields.io/badge/Visualization-Cytoscape.js-brightgreen)](https://js.cytoscape.org/)
[![Compliance](https://img.shields.io/badge/Legal_Framework-BNSS_2023_Section_94%2F106-blue)]()
[![Integrity](https://img.shields.io/badge/Integrity-Tamper--Evident_SHA--256_Record-blueviolet)]()

> **Smart India Hackathon (SIH 2026)**
> **Problem Statement ID**: `SIH26182`
> **Problem Statement Title**: *Automated Attribution of Unknown Cryptocurrency Wallets to Nearest Virtual Asset Service Providers (VASPs) through Blockchain Intelligence APIs*
> **Theme**: Blockchain & Cybersecurity | **Category**: Software
> **Team**: Achievers | **Target Users**: Law Enforcement Agencies (LEAs) & Cyber Crime Cells

> **⚠️ OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER**
> This prototype uses pre-seeded synthetic data with SIM- prefixed transaction IDs.
> No live blockchain connectivity is present. All attributions are based on a curated
> demo VASP registry. Live provider integration (TronGrid, Etherscan) is Phase 2.

---

## 📌 1. Problem Overview & Real-World Challenge

In modern financial cybercrime (loan app extortion, Telegram task scams, ransomware), criminals convert stolen victim funds into cryptocurrency (e.g., USDT) on private, unhosted wallets. To evade detection, they route funds across multiple intermediary mule wallets (layering) before depositing into centralized crypto exchanges (VASPs) like CoinDCX or Binance.

### The Core Law Enforcement Bottleneck:
* Law enforcement officers tracing on-chain transactions only see raw, unhosted wallet addresses.
* Under the government's **I4C SAHYOG platform**, over **45+ crypto exchanges** are registered to assist with lawful information requests.
* **The Challenge**: The investigating officer has **no automated way to determine which of the 45+ exchanges received the stolen funds**, causing critical multi-day delays during which criminals cash out.

---

## ⚡ 2. What Has Been Built & Is Fully Operational Today

**VASP TRACE** provides an end-to-end, multi-screen investigative portal that automates the forensic chain:
`TRACE ➔ ATTRIBUTE ➔ EXPLAIN ➔ CORRELATE ➔ DRAFT REQUEST (SAHYOG) ➔ VERIFY`.

### 🚀 Key Functional Modules:

1. **👮 Screen 1: Investigator Identity Gateway**:
   * Role-based officer session (CCTNS/SAHYOG compatible login format).

2. **📁 Screen 2: Active FIR & Investigation Dashboard**:
   * Centralized FIR intake registry displaying metrics (Active FIRs, Tracked Stolen Volume, SAHYOG Drafts, Infrastructure Overlaps).
   * 1-Click case selection for pre-seeded case investigations and custom suspect wallet entry.

3. **🕸️ Screen 3: Interactive Multi-Hop Graph Traversal Engine**:
   * In-memory directed graph construction using **Python & NetworkX** ($G = (V, E)$).
   * **BFS traversal** with hard `max_hops` bound enforced during traversal, per-path cycle prevention, and duplicate transfer deduplication.
   * **Cytoscape.js Interactive Canvas** with dynamic node inspectors, risk badges, and animated fund-flow arrows.

4. **🎯 Explainable VASP Attribution Engine (4-Stage Pipeline)**:
   * Stage 1: Candidate discovery via `entity_intelligence` — the single authoritative source for VASP address resolution.
   * Stage 2: Label conflict detection — conflicting VASP labels are surfaced, never silently resolved.
   * Stage 3: 6-Factor Weighted Scoring Formula:
     $$\text{Score} = 100 \times (W_F \cdot F + W_P \cdot P + W_T \cdot T + W_L \cdot L + W_S \cdot S + W_I \cdot I)$$
     where F=flow relevance, P=hop proximity, T=temporal velocity, L=label strength, S=sweep evidence, I=independent corroboration.
   * Stage 4: Selection in **hop order** (earliest qualifying VASP wins, not highest-scoring).
   * No case-ID-based logic: identical evidence always produces identical scores.
   * Explicit "no qualifying VASP found" result if threshold not met — never a forced match.
   * Per-factor breakdown with evidence gaps/limitations on every result.

5. **⚠️ Cross-Case Infrastructure Correlation Engine**:
   * Persistent cross-case intelligence graph scanning historical FIR databases for recurring shared wallet infrastructure across different police jurisdictions.
   * Language: "shared infrastructure", "recurring intermediary", "analyst review required" — NOT "syndicate detection" or implied proof of organized crime.

6. **🤝 Lawful SAHYOG Requisition Drafter**:
   * Draft lawful requisitions under **BNSS 2023** (Bharatiya Nagarik Suraksha Sanhita):
     * **Section 94**: Summons to produce document/thing (KYC, transaction logs).
     * **Section 106**: Preservation and potential seizure — requires authorized investigator; NOT an automated account-freeze mechanism.
     * **Section 107**: Attachment/forfeiture — requires court order; applicable only where legally relevant.
   * All outputs are **DRAFT** status requiring authorized investigator and legal process review.

7. **📑 Official Printable Forensic Investigation Report**:
   * Structured step-by-step transaction table.
   * **Tamper-Evident Technical Integrity Record** sealed with SHA-256 checksum.
   * Interactive Hash Integrity Verifier Tool.
   * NOTE: This is a technical integrity record, not a Section 65B IEA certificate.

8. **🌐 FATF Recommendation 16 / Virtual Asset Compliance Context**:
   * FATF Recommendation 16 (and virtual-asset provisions under Recommendation 15) require qualifying VASP-to-VASP transfers to carry originator/beneficiary information, obtained, held, transmitted, and made available to appropriate authorities.
   * VASPTRACE complements this by tracing on-chain movement and identifying a likely VASP endpoint to inform a lawful information request — it does **not** itself identify wallet ownership and is **not** the Travel Rule mechanism.

---

## 🏗️ 3. System Architecture & Data Pipeline

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                INVESTIGATOR WORKBENCH                                  │
│                 (Responsive Dark Cyberpunk UI • Cytoscape.js Canvas)                   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ REST API
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI ORCHESTRATION LAYER                               │
│                   (/api/trace • /api/cases • /api/sahyog • /api/verify)                │
└───────┬───────────────────────────────────┬────────────────────────────────┬───────────┘
        │                                   │                                │
        ▼                                   ▼                                ▼
┌──────────────────────┐         ┌──────────────────────┐         ┌──────────────────────┐
│  GRAPH ENGINE        │         │ ATTRIBUTION ENGINE   │         │ CROSS-CASE ENGINE    │
│  (NetworkX BFS)      │ ──────➔ │ (4-Stage Pipeline)   │ ──────➔ │ (Infrastructure      │
│  • Hard max_hops     │         │ • entity_intelligence│         │  Correlation)        │
│  • Cycle prevention  │         │ • 6-Factor Scoring   │         │  Analyst review req  │
└──────────────────────┘         └──────────────────────┘         └──────────────────────┘
        │                                   │                                │
        └───────────────────────────────────┼────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       GROUND TRUTH & EVIDENCE SECURITY LAYER                           │
│  • VASP Entity Registry (entity_intelligence + known_vasp_directory.json)              │
│  • SAHYOG Lawful Draft Router (BNSS 2023 Section 94 / 106 / 107)                       │
│  • SHA-256 Tamper-Evident Technical Integrity Record                                   │
│  • Provider Abstraction: SyntheticDemoProvider (live: Phase 2 TronGrid/Etherscan stubs)│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 4. Repository Structure

```text
SIH-2026-VASP-TRACE/
├── backend/
│   ├── app.py                   # FastAPI REST server & API endpoints
│   ├── graph_engine.py          # NetworkX BFS directed graph traversal (VASP-agnostic)
│   ├── attribution_engine.py    # 4-Stage explainable VASP attribution (no case-ID logic)
│   ├── entity_intelligence.py   # Single source for VASP address label resolution
│   ├── cross_case_engine.py     # Cross-case infrastructure correlation index
│   ├── sahyog_router.py         # BNSS 2023 Section 94/106/107 lawful draft generator
│   ├── evidence_verifier.py     # SHA-256 tamper-evident technical integrity record
│   ├── mock_blockchain.py       # OFFLINE DEMO synthetic ledger (SIM- tx IDs)
│   ├── models.py                # Pydantic v2 data models, DB preparation models
│   └── providers/               # Blockchain provider abstraction
│       ├── __init__.py
│       ├── blockchain_provider.py  # Abstract base class
│       ├── synthetic_demo.py       # Demo/offline provider (currently active)
│       ├── trongrid_provider.py    # STUB ONLY — Phase 2
│       └── etherscan_provider.py   # STUB ONLY — Phase 2
├── frontend/
│   ├── index.html               # 3-Screen Law Enforcement Command Portal
│   └── static/
│       ├── css/styles.css       # Cyber dark command theme & print stylesheets
│       └── js/
│           ├── app.js           # Multi-screen controller & API integration
│           └── graph.js         # Cytoscape.js graph renderer & layout styles
├── datasets/
│   ├── known_vasp_directory.json # VASP entity registry (hot wallets, FIU-IND metadata)
│   ├── demo_dataset_test.py      # Dataset validation script
│   └── DATASETS_GUIDE_AND_DOWNLOADS.md # External dataset references
├── .gitignore
├── README.md                    # Project documentation
└── run_demo.bat                 # 1-Click local launcher for Windows
```

---

## 🚀 5. How to Run Locally

### Prerequisites:
* Python 3.9+ installed
* Modern Web Browser (Chrome, Edge, Brave, Firefox)

### Steps:
1. **Clone the repository**:
   ```bash
   git clone https://github.com/harshalpatil2031-ui/SIH-2026-VASP-TRACE.git
   cd SIH-2026-VASP-TRACE
   ```
2. **Install Python dependencies**:
   ```bash
   pip install fastapi uvicorn networkx pydantic httpx
   ```
3. **Launch the platform**:
   * On Windows: Double-click **`run_demo.bat`**
   * Or via terminal:
     ```bash
     python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
     ```
4. **Open in Browser**: Navigate to **`http://localhost:8000`**.

---

## 🛣️ 6. Current Milestones vs. Phase 2 Roadmap

| Milestone / Feature | Status | Implementation Details |
| :--- | :---: | :--- |
| **3-Screen Multi-View Portal** | ✅ Complete | Investigator login ➔ Case directory ➔ Analysis workbench |
| **NetworkX BFS Graph Traversal** | ✅ Complete | Hard max_hops bound, cycle prevention, deduplication |
| **Cytoscape Visual Canvas** | ✅ Complete | Interactive node inspector, zoom/pan & animated flow edges |
| **4-Stage Attribution Engine** | ✅ Complete | 6-Factor scoring, no case-ID logic, hop-order selection, label conflict detection |
| **Entity Intelligence Layer** | ✅ Complete | Single authoritative VASP address resolver, Phase 2 API hooks documented |
| **Cross-Case Infrastructure Correlation** | ✅ Complete | Flags shared intermediary wallets across FIRs (analyst review required) |
| **BNSS 2023 SAHYOG Draft Generator** | ✅ Complete | Section 94/106/107 — DRAFT only, investigator approval required |
| **Tamper-Evident Integrity Record** | ✅ Complete | SHA-256 over canonical payload; separate from presentation metadata |
| **Provider Abstraction Layer** | ✅ Complete | SyntheticDemoProvider active; TronGrid/Etherscan stubs for Phase 2 |
| **DB Preparation Models** | ✅ Complete | Pydantic models for future PostgreSQL migration (no persistence wired) |
| **Live Blockchain RPC Adapters** | 🔄 Phase 2 | TronGrid/Etherscan stubs ready; actual API wiring in Phase 2 |
| **Cross-Chain Bridge Heuristics** | 🔄 Phase 2 | Tracking Wormhole/Thorchain cross-chain swaps |
| **PostgreSQL Persistence** | 🔄 Phase 2 | DB models prepared; migration not yet wired |

---

## ⚠️ 7. Important Limitations & Disclaimers

* **OFFLINE DEMONSTRATION ONLY**: All blockchain data in this prototype is synthetic (SIM- prefixed IDs). No live blockchain data is accessed.
* **Attribution is probabilistic**: VASPTRACE identifies a *likely* VASP endpoint — it does not prove wallet ownership or legal liability. Findings require investigator review.
* **Not a legal certificate**: The SHA-256 tamper-evident integrity record is a technical integrity check, not a Section 65B IEA certificate or court-admissible evidence certification.
* **Not an automated account freeze**: The SAHYOG draft generator produces a DRAFT lawful requisition only. No account freeze or legal action is automatically triggered. Authorized investigator and proper legal process are required.
* **Cross-case correlation ≠ proof of organized crime**: Shared infrastructure across cases requires analyst review — it does not automatically prove a criminal syndicate.

---

## 👥 Team Achievers
* **Project Lead & Developer**: Harshal Patil (SP • Cyber Crime Unit)
* **Problem Statement**: SIH26182 (Smart India Hackathon 2026)
