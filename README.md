# 🛡️ VASP TRACE: Automated Cryptocurrency Wallet Attribution & Cross-Case Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![NetworkX](https://img.shields.io/badge/Graph_Engine-NetworkX-orange)](https://networkx.org/)
[![Cytoscape.js](https://img.shields.io/badge/Visualization-Cytoscape.js-brightgreen)](https://js.cytoscape.org/)
[![Compliance](https://img.shields.io/badge/Legal_Compliance-Sec_91%2F102_CrPC-red)]()
[![Security](https://img.shields.io/badge/Integrity-Section_65B_IEA_SHA--256-blueviolet)]()

> **Smart India Hackathon (SIH 2026)**  
> **Problem Statement ID**: `SIH26182`  
> **Problem Statement Title**: *Automated Attribution of Unknown Cryptocurrency Wallets to Nearest Virtual Asset Service Providers (VASPs) through Blockchain Intelligence APIs*  
> **Theme**: Blockchain & Cybersecurity | **Category**: Software  
> **Team**: Achievers | **Target Users**: Law Enforcement Agencies (LEAs) & Cyber Crime Cells

---

## 📌 1. Problem Overview & Real-World Challenge

In modern financial cybercrime (loan app extortion, Telegram task scams, ransomware), criminals convert stolen victim funds into cryptocurrency (e.g., USDT) on private, unhosted wallets. To evade detection, they route funds across multiple intermediary mule wallets (layering) before depositing into centralized crypto exchanges (VASPs) like CoinDCX or Binance.

### The Core Law Enforcement Bottleneck:
* Law enforcement officers tracing on-chain transactions only see raw, unhosted wallet addresses.
* Under the government's **I4C SAHYOG platform**, over **45+ crypto exchanges** are registered to execute account freezes.
* **The Challenge**: The investigating officer has **no automated way to determine which of the 45+ exchanges received the stolen funds**, causing critical multi-day delays during which criminals cash out.

---

## ⚡ 2. What Has Been Built & Is Fully Operational Today

**VASP TRACE** provides an end-to-end, multi-screen investigative portal that automates the entire forensic chain:  
`TRACE ➔ ATTRIBUTE ➔ EXPLAIN ➔ CORRELATE ➔ ROUTE (SAHYOG) ➔ VERIFY`.

### 🚀 Key Functional Modules:

1. **👮 Screen 1: Investigator Identity Gateway**:
   * Role-Based Access Control (RBAC) supporting CCTNS/SAHYOG officer session authentication (`harshalpatil.2031@gmail.com • SP Cyber Unit`).

2. **📁 Screen 2: Active FIR & Investigation Dashboard**:
   * Centralized FIR intake registry displaying real-time metrics (Active FIRs, Tracked Stolen Volume in INR/Crypto, SAHYOG Dispatches, Syndicate Matches).
   * 1-Click case selection for pre-seeded case investigations and custom suspect wallet entry.

3. **🕸️ Screen 3: Interactive Multi-Hop Graph Traversal Engine**:
   * In-memory directed graph construction using **Python & NetworkX** ($G = (V, E)$).
   * **Cytoscape.js Interactive Canvas** with dynamic node inspectors, risk badges, and animated fund-flow arrows across suspect, intermediary mules, deposit addresses, and exchange vaults.

4. **🎯 Explainable VASP Attribution Engine**:
   * Detects centralized **Deposit Consolidation Sweeps** into master exchange hot vaults.
   * Computes a **4-Factor Weighted Attribution Confidence Model**:
     $$\text{Confidence} = w_1(\text{Flow Volume \%}) + w_2(\text{Sweep Match}) + w_3(\text{Hop Proximity}) + w_4(\text{Velocity})$$
   * Transparent proof factors displayed directly to the investigator ("Why this VASP?").

5. **⚠️ Cross-Case Syndicate Correlation Engine**:
   * Persistent cross-case intelligence graph that scans historical FIR databases to detect recurring middleman wallets shared across different police jurisdictions (e.g., linking Case #147 to Mumbai Case #101).

6. **🤝 Lawful SAHYOG Requisition Dispatcher**:
   * Automated legal notice drafting under **Section 91 & 102 CrPC** to issue immediate 72-hour freezing orders to the identified exchange compliance officer.

7. **📑 Official Printable Forensic Police Report**:
   * Ready-to-print court report with structured step-by-step transaction table (`Hop #1 ➔ Hop #2 ➔ Deposit ➔ Vault Sweep`).
   * **Section 65B Indian Evidence Act / Section 63 BSA 2023 Digital Certificate** sealed with a cryptographic **SHA-256 tamper-proof hash**.
   * Interactive **Hash Integrity Verifier Tool** to prove evidence has not been tampered with.

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
└───────┬───────────────────────────────────┬────────────────────────────────────┬───────┘
        │                                   │                                    │
        ▼                                   ▼                                    ▼
┌──────────────────────┐         ┌──────────────────────┐         ┌──────────────────────┐
│  GRAPH ENGINE        │         │ ATTRIBUTION ENGINE   │         │ CROSS-CASE ENGINE    │
│  (NetworkX DiGraph)  │ ──────➔ │ (4-Factor Scoring &  │ ──────➔ │ (Syndicate Mapping & │
│  • Peeling-chain flow│         │  Deposit Sweep Match)│         │  Historical FIR Link)│
└──────────────────────┘         └──────────────────────┘         └──────────────────────┘
        │                                   │                                    │
        └───────────────────────────────────┼────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       GROUND TRUTH & EVIDENCE SECURITY LAYER                           │
│  • Verified VASP Registry (CoinDCX, Binance, WazirX, CoinSwitch, ZebPay, KuCoin)       │
│  • SAHYOG Legal Notice Dispatch Router (Section 91 / 102 CrPC)                         │
│  • SHA-256 Cryptographic Evidence Seal (Section 65B IEA / BSA 2023)                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 4. Repository Structure

```text
SIH-2026-VASP-TRACE/
├── backend/
│   ├── app.py                   # FastAPI REST server & API endpoints
│   ├── graph_engine.py          # NetworkX directed graph traversal & flow analysis
│   ├── attribution_engine.py    # Explainable 4-factor VASP attribution algorithm
│   ├── cross_case_engine.py     # Multi-case syndicate correlation index
│   ├── sahyog_router.py         # Section 91/102 CrPC SAHYOG notice generator
│   ├── evidence_verifier.py     # SHA-256 Section 65B forensic hash engine
│   ├── mock_blockchain.py       # Pre-seeded topological transaction datasets
│   └── models.py                # Pydantic v2 data models & schemas
├── frontend/
│   ├── index.html               # 3-Screen Law Enforcement Command Portal
│   └── static/
│       ├── css/styles.css       # Cyber dark command theme & print stylesheets
│       └── js/
│           ├── app.js           # Multi-screen controller & API integration
│           └── graph.js         # Cytoscape.js graph renderer & layout styles
├── datasets/
│   ├── known_vasp_directory.json # Verified exchange hot vaults & FIU-IND metadata
│   └── DATASETS_GUIDE_AND_DOWNLOADS.md # External dataset references & documentation
├── .gitignore                   # Ignored local temporary & presentation files
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
| **NetworkX Graph Traversal** | ✅ Complete | Dynamic multi-hop flow calculation & path tracing |
| **Cytoscape Visual Canvas** | ✅ Complete | Interactive node inspector, zoom/pan & animated flow edges |
| **Explainable Attribution Engine** | ✅ Complete | 4-Factor mathematical scoring + deposit sweep matching |
| **Cross-Case Syndicate Detection** | ✅ Complete | Flags shared intermediary wallets across multiple FIRs |
| **I4C SAHYOG Notice Generator** | ✅ Complete | Structured Section 91 & 102 CrPC legal notice workflow |
| **Section 65B Forensic Report** | ✅ Complete | Ready-to-print official police report with SHA-256 seal |
| **Live Blockchain RPC Adapters** | 🔄 Phase 2 | Plugging in live Alchemy/TronGrid WebSocket streaming |
| **Cross-Chain Bridge Heuristics** | 🔄 Phase 2 | Tracking Wormhole/Thorchain cross-chain swaps |

---

## 👥 Team Achievers
* **Project Lead & Developer**: Harshal Patil (SP • Cyber Crime Unit)
* **Problem Statement**: SIH26182 (Smart India Hackathon 2026)
