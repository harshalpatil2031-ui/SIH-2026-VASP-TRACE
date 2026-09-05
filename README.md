# 🔍 VASP TRACE: Automated Cryptocurrency Wallet Attribution & Cross-Case Intelligence Platform

> **Problem Statement ID**: `SIH26182`  
> **Problem Statement Title**: *Automated Attribution of Unknown Cryptocurrency Wallets to Nearest Virtual Asset Service Providers (VASPs) through Blockchain Intelligence APIs*  
> **Theme**: Blockchain & Cybersecurity | **Category**: Software  
> **Team**: Achievers | **Platform**: Government Law Enforcement / I4C SAHYOG Compliance

---

## 📌 Executive Summary
**VASP TRACE** is an explainable, graph-based cryptocurrency forensic intelligence engine designed for Indian Law Enforcement Agencies (LEAs) and Cyber Crime Units. 

When cybercriminals launder stolen victim funds through unhosted multi-hop peeling chains into centralized crypto exchanges, **VASP TRACE** automates:
1. **Multi-Chain Graph Traversal** across TRON, Ethereum, Bitcoin, and Solana.
2. **Centralized Deposit Sweep Detection** to attribute unknown destination accounts to verified exchange hot vaults.
3. **Cross-Case Syndicate Correlation** linking shared middleman infrastructure across isolated police FIRs.
4. **I4C SAHYOG Freezing Notices** under Section 91 & 102 CrPC.
5. **Section 65B Indian Evidence Act Cryptographic Integrity Seals** (SHA-256).

---

## 🏗️ Technical Architecture & Stack

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│   1. Investigator UI      │ ───➔ │  2. API Orchestration     │ ───➔ │  3. Blockchain Ingestion  │
│  (Tailwind + Cytoscape.js)│      │     (FastAPI / Python)    │      │    (TronGrid / Etherscan) │
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
                                                 │
                                                 ▼
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│   6. Output & Compliance  │ ◄─── │  5. Intelligence Layer    │ ◄─── │  4. Graph Traversal Engine│
│  (SAHYOG + Section 91 CrPC│      │ (Cross-Case Syndicate DB) │      │  (NetworkX Directed Graph)│
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

* **Backend Engine**: Python 3.10+, FastAPI, NetworkX (Graph Algorithms), Pydantic v2
* **Frontend UI**: Responsive 3-Screen Dark Command Portal, Cytoscape.js (Interactive Graph Canvas), Tailwind CSS
* **Database & Evidence**: SQLite/PostgreSQL, SHA-256 Tamper-Proof Cryptographic Engine
* **Ground Truth Intelligence**: Verified VASP clusters for CoinDCX, WazirX, Binance, CoinSwitch, ZebPay, and KuCoin.

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
* Python 3.9+ installed
* Modern Web Browser (Chrome, Edge, Brave)

### 1. Clone the Repository
```bash
git clone https://github.com/harshalpatil2031-ui/SIH-2026-VASP-TRACE.git
cd SIH-2026-VASP-TRACE
```

### 2. Install Dependencies
```bash
pip install -r - <<EOF
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
networkx>=3.0
httpx>=0.24.0
EOF
```

### 3. Run the Platform
Double-click **`run_demo.bat`** (on Windows) or run:
```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to: **`http://localhost:8000`** in your browser.

---

## ⚖️ Legal & Forensic Compliance
* **Section 91 & 102 CrPC Requisition Formatting**: Automated disclosure and asset freezing notice generation.
* **Section 65B Indian Evidence Act / Section 63 BSA 2023 Compliance**: Cryptographic hash certificate ensuring electronic record authenticity and non-repudiation.
* **FIU-IND Reporting Alignment**: Mapping target entities to registered Indian Virtual Digital Asset service providers.

---

## 👥 Team Achievers (SIH 2026)
* **Lead / Developer**: Harshal Patil
* **Domain**: Cybersecurity, Blockchain Forensics & Law Enforcement Intelligence
