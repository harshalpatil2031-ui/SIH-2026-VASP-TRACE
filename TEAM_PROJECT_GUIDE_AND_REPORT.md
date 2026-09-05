# 📘 VASP TRACE: Comprehensive Team Master Report & Technical Documentation

> **Project Name**: VASP TRACE  
> **Smart India Hackathon (SIH 2026)** — Problem Statement ID: `SIH26182`  
> **Problem Statement Title**: *Automated Attribution of Unknown Cryptocurrency Wallets to Nearest Virtual Asset Service Providers (VASPs) through Blockchain Intelligence APIs*  
> **Team Name**: Achievers | **Project Lead**: Harshal Patil  
> **Target Audience**: Team Members, Evaluators, and Technical Collaborators  

---

## 📑 TABLE OF CONTENTS
1. [Executive Summary & The Real-World Crime Scenario](#1-executive-summary--the-real-world-crime-scenario)
2. [Core Terminology Explained in Simple English](#2-core-terminology-explained-in-simple-english)
3. [The 4 Unique Value Propositions (UVP)](#3-the-4-unique-value-propositions-uvp)
4. [Complete System Architecture & 9-Step Data Pipeline](#4-complete-system-architecture--9-step-data-pipeline)
5. [Technical Deep-Dive: How the Code Works (Module by Module)](#5-technical-deep-dive-how-the-code-works-module-by-module)
6. [The 3-Screen User Interface & Investigator Workflow](#6-the-3-screen-user-interface--investigator-workflow)
7. [Feasibility, Key Challenges & Our Technical Mitigations](#7-feasibility-key-challenges--our-technical-mitigations)
8. [Legal & Cyber Forensics Compliance (CrPC & IEA)](#8-legal--cyber-forensics-compliance-crpc--iea)
9. [Team Git Collaboration & Pull Request (PR) Workflow](#9-team-git-collaboration--pull-request-pr-workflow)

---

## 1. Executive Summary & The Real-World Crime Scenario

### 🎯 The Real Problem in Cyber Crime Police Cells:
Imagine an Indian citizen loses **₹1,80,000** (or ₹50,000) in an instant fake loan app extortion or Telegram task scam.
* Criminals do **not** keep stolen money in Indian bank accounts because cyber police freeze bank accounts via 1930 within hours.
* Instead, criminals immediately convert that money into **cryptocurrency (USDT)** on private, unhosted wallets.
* To confuse investigators, they bounce the crypto through 2 or 3 intermediary "mule" wallets (layering) before depositing it into a centralized crypto exchange like **CoinDCX, Binance, or WazirX** to cash out into fiat currency.

### 🛑 The Law Enforcement Bottleneck:
* The police officer logs into the **I4C SAHYOG portal** (Ministry of Home Affairs), where **over 45+ crypto exchanges** are connected to freeze criminal accounts.
* **The Dead End**: The officer only sees an unhosted wallet address (e.g., `TJ9kLpBw...`). **The officer has NO IDEA which of the 45+ exchanges on SAHYOG actually received the victim's money!**
* Tracing this manually across blockchain explorers takes days, and by then, the criminals have already withdrawn the funds.

### 💡 What VASP TRACE Does:
**VASP TRACE** takes that unknown suspect wallet address, automatically traces the multi-hop path across blockchains in seconds, mathematically attributes the destination crypto exchange with an explainable confidence score, connects the wallet to existing cross-case syndicates, and generates the ready-to-dispatch **Section 91 & 102 CrPC freezing requisition** for the SAHYOG portal!

---

## 2. Core Terminology Explained in Simple English

| Term | Full Form / Meaning | Simple Analogy / Explanation |
| :--- | :--- | :--- |
| **VASP** | **Virtual Asset Service Provider** | Centralized crypto exchanges (CoinDCX, Binance, WazirX, CoinSwitch) where users trade, deposit, and cash out crypto to bank accounts. |
| **Unhosted Wallet** | Private Non-Custodial Wallet | A personal wallet (like MetaMask, TrustWallet) that is not linked to any KYC or exchange identity. |
| **Peeling Chain / Mule** | Multi-hop Fund Layering | Scammers moving money from Wallet A ➔ Wallet B ➔ Wallet C in rapid succession to hide origin. |
| **Deposit Address** | Unique User Account Wallet | The temporary address an exchange assigns to a specific customer to deposit crypto. |
| **Consolidation Sweep** | Internal Exchange Transfer | When an exchange automatically moves funds from a customer's deposit address into the exchange's master hot/cold vault. |
| **Hot Vault** | Master Exchange Liquidity Wallet | The verified main public wallet of the exchange that holds aggregated customer balances. |
| **I4C SAHYOG** | MHA Law Enforcement Gateway | The official government portal connecting Indian police with 45+ crypto exchanges for legal requisitions. |
| **Section 91 / 102 CrPC** | Code of Criminal Procedure | The legal sections Indian police use to summon data (Sec 91) and freeze/seize criminal property (Sec 102). |
| **Section 65B IEA** | Indian Evidence Act Certificate | The legal certificate & SHA-256 digital seal proving electronic evidence has not been tampered with. |

---

## 3. The 4 Unique Value Propositions (UVP)

*(As presented in Slide 2 of our official SIH PPT)*

1. **Explainable Attribution**: We don't just output a blind exchange name. We provide transparent mathematical proof (Flow volume %, Deposit sweep verification, Hop proximity, and Speed).
2. **Cross-Case Intelligence**: We correlate intermediary mule wallets across previous FIRs in our database. If a wallet was used in Mumbai last week and Hyderabad today, we unmask the shared syndicate!
3. **Intelligent Request Routing**: Recommends the exact next legal action (e.g., `🟠 Preservation Request` vs `KYC Disclosure Requisition`).
4. **Evidence Integrity**: Every investigation report is sealed with a **SHA-256 cryptographic hash** guaranteeing courtroom admissibility under Section 65B of the Indian Evidence Act / Section 63 BSA 2023.

---

## 4. Complete System Architecture & 9-Step Data Pipeline

*(Directly mapped to Slide 3 of our official SIH PPT)*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: USER INTERFACE                                                                │
│  Investigator inputs Case ID, Suspect Wallet, Chain & FIR Details                     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP POST /api/trace
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: BACKEND & API ORCHESTRATION (FastAPI + Python)                                │
│  Validates parameters, manages session, and triggers async forensic pipeline           │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: BLOCKCHAIN DATA ACQUISITION LAYER                                             │
│  Ingests multi-hop transaction blocks via APIs (TronGrid, Etherscan, Bitquery, Alchemy)│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: GRAPH ENGINE (NetworkX Directed Graph + Neo4j Storage)                        │
│  Constructs G = (V, E) where Wallets = Nodes, Transactions = Directed Edges            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: EXPLAINABLE ATTRIBUTION ENGINE                                                │
│  • Traverses all simple paths from suspect node to terminal nodes                      │
│  • Detects "Consolidation Sweep" into master exchange hot vaults                       │
│  • Computes 4-Factor Weighted Confidence Score (Volume, Sweep, Hops, Velocity)         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: INTELLIGENCE LAYER & CROSS-CASE CORRELATION                                   │
│  Scans historical database for shared intermediary mule wallets across other FIRs      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 7: EVIDENCE INTEGRITY & TAMPER-PROOF SEAL (evidence_verifier.py)                 │
│  Computes SHA-256 cryptographic checksum of structured evidence payload                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 8: SAHYOG LAWFUL ROUTING ENGINE (sahyog_router.py)                               │
│  Drafts Section 91 & 102 CrPC Freezing Requisition to Exchange Nodal Compliance Officer│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STEP 9: INVESTIGATOR OUTPUT WORKBENCH                                                 │
│  Cytoscape Visual Graph + Explainability Proof + SAHYOG Notice Modal + Printable Report│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Technical Deep-Dive: How the Code Works (Module by Module)

### 📁 Backend Architecture (`backend/`):

#### 1. `backend/app.py` (FastAPI REST Server)
* Serves the REST API endpoints:
  * `POST /api/trace`: Runs multi-hop traversal and attribution for a given wallet.
  * `GET /api/cases/{case_id}`: Retrieves pre-seeded case parameters.
  * `POST /api/sahyog/dispatch`: Simulates dispatching legal notice to the exchange.
  * `POST /api/evidence/verify`: Validates whether a SHA-256 hash has been modified.
* Serves the static frontend assets from `frontend/`.

#### 2. `backend/graph_engine.py` (NetworkX Graph Traversal Engine)
* Constructs an in-memory **Directed Graph** (`nx.DiGraph`).
* Uses `nx.all_simple_paths()` to discover all possible paths from the suspect wallet to terminal deposit addresses.
* Calculates out-degree volume, fee retention by mules, and hop distance.

#### 3. `backend/attribution_engine.py` (Explainable Attribution Algorithm)
* **The Sweep Heuristic**: Centralized exchanges do not leave customer deposits in deposit wallets. An automated internal script sweeps funds to the master exchange vault.
* Calculates the 4 explainability factors:
  1. **Flow Volume Match** (How much of the stolen money reached the exchange).
  2. **Exchange Sweep Verification** (Matches destination vault with our verified VASP registry).
  3. **Hop Distance** (Number of intermediary transfers).
  4. **Transfer Velocity** (Speed of movement in minutes).
* Outputs primary candidate (e.g. **CoinDCX 96% Confidence**) and secondary candidate rankings.

#### 4. `backend/cross_case_engine.py` (Cross-Case Syndicate Index)
* Maintains a reverse index mapping wallet addresses to historical police FIRs.
* When middleman wallet `0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C` is detected, it immediately flags that this wallet was involved in **Mumbai Case #101**, linking the cases into a single criminal network.

#### 5. `backend/sahyog_router.py` (SAHYOG Notice Generator)
* Formats legal freezing notices under **Section 91 and 102 CrPC**.
* Matches the identified VASP with its registered **FIU-IND Nodal Compliance Officer Email** (e.g., `nodalofficer@coindcx.com`).
* Generates a 72-hour escrow account freeze ticket.

#### 6. `backend/evidence_verifier.py` (Section 65B SHA-256 Seal)
* Computes deterministic SHA-256 checksums of the entire transaction trail.
* Validates whether submitted evidence has remained unmodified for courtroom presentation.

#### 7. `backend/mock_blockchain.py` & `datasets/known_vasp_directory.json`
* Contains ground-truth hot vault addresses, deposit patterns, and FIU registration numbers for top exchanges: **CoinDCX, Binance, WazirX, CoinSwitch, ZebPay, and KuCoin**.

---

### 🎨 Frontend Architecture (`frontend/`):

* **`frontend/index.html`**: Structured into 3 distinct screen containers (`#screenLogin`, `#screenDashboard`, `#screenAnalysis`).
* **`frontend/static/js/app.js`**: Controls the multi-screen transitions, terminal progress animations, and modal interactions.
* **`frontend/static/js/graph.js`**: Cytoscape.js visual graph renderer configuring node colors (Red = Suspect, Amber = Mule, Purple = Deposit, Green = VASP Vault), edge labels, and breadth-first layout animations.
* **`frontend/static/css/styles.css`**: Cyber dark command aesthetic with glowing cyan/emerald borders and `@media print` rules for the police report.

---

## 6. The 3-Screen User Interface & Investigator Workflow

```
┌─────────────────────────────────┐
│ SCREEN 1: LOGIN GATEWAY         │
│ • Officer Email & Badge         │
│ • CCTNS / SAHYOG Verification   │
└────────────────┬────────────────┘
                 │ Click Authenticate
                 ▼
┌─────────────────────────────────┐
│ SCREEN 2: CASE DASHBOARD        │
│ • 4 KPI Stats Cards             │
│ • Case Intake Form (Left)       │
│ • Previous FIR Registry (Right) │
└────────────────┬────────────────┘
                 │ Click Analyze Case #147
                 ▼
┌─────────────────────────────────┐
│ SCREEN 3: ANALYSIS WORKBENCH    │
│ • Animated Terminal Sequence    │
│ • Cytoscape Multi-Hop Graph     │
│ • VASP Attribution Card (96%)   │
│ • Cross-Case Syndicate Alert    │
│ • SAHYOG Freezing Notice Modal  │
│ • Printable Police Report Modal │
│ • SHA-256 Hash Verifier Modal   │
└─────────────────────────────────┘
```

---

## 7. Feasibility, Key Challenges & Our Technical Mitigations

*(Directly mapped to Slide 4 of our official SIH PPT)*

| Key Challenge | Real-World Risk | How VASP TRACE Solves It (Mitigation) |
| :--- | :--- | :--- |
| **1. Large Transaction Graphs** | Thousands of transactions causing browser/memory freeze. | **Heuristic Depth Pruning**: Limits traversal to 5 hops and ignores dust transactions under a value threshold. |
| **2. Unknown Wallet Ownership** | Unhosted wallets have no KYC identity tags. | **Deposit Sweep Heuristic**: Combines wallet clustering, flow volume, and sweep patterns rather than relying on static tags. |
| **3. False VASP Attribution** | Mistakenly accusing the wrong crypto exchange. | **Confidence-Based Candidate Ranking**: Displays transparent probability distributions and alternative candidate rankings. |
| **4. Cross-Chain Complexity** | Scammers using multiple blockchains (TRON, ETH, BTC). | **Modular Chain Adapters**: Normalizes all chains into a standard unified Node/Edge schema. |
| **5. Venue Demo API Failure** | Live APIs failing on stage due to bad venue Wi-Fi or rate limits. | **Local Verified Cluster Caching**: High-speed, zero-latency local execution ensuring 100% demo stability. |

---

## 8. Legal & Cyber Forensics Compliance (CrPC & IEA)

In real law enforcement operations, technical data is useless if it is rejected by a judge in court. VASP TRACE is strictly engineered for Indian legal compliance:

1. **Section 91 CrPC (Summons to Produce Documents)**:
   * Requisition issued to the crypto exchange to provide KYC records, IP login logs, and bank account links of the deposit wallet owner.
2. **Section 102 CrPC (Power of Police to Seize Property)**:
   * Direct order to the crypto exchange to freeze the target wallet balance in escrow for 72 hours.
3. **Section 65B Indian Evidence Act / Section 63 Bharatiya Sakshya Adhiniyam (BSA 2023)**:
   * Mandates electronic evidence integrity. Sealed with a SHA-256 hash stamp to prove the transaction logs were never modified.
4. **No Generative AI / LLM Hallucinations**:
   * All reports are compiled deterministically from mathematical graph edges — zero risk of AI hallucinating fake wallet addresses in court!

---

## 9. Team Git Collaboration & Pull Request (PR) Workflow

Our repository is protected under **GitHub Rulesets**. No one can push directly to `main`. All teammates must follow this professional Git workflow:

```
┌─────────────────────────────────┐
│ 1. Clone Repo & Create Branch   │ git checkout -b feature/your-feature-name
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 2. Write Code & Test Locally    │ python backend/app.py (run_demo.bat)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 3. Commit & Push Branch         │ git push origin feature/your-feature-name
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ 4. Open Pull Request on GitHub  │ Admin (Harshal) reviews & merges into main
└─────────────────────────────────┘
```

---

### 🏆 Summary:
Team Achievers has a complete, working, and legally sound solution for **Problem Statement SIH26182**. Use this documentation to understand the architecture, explain the system to mentors/judges, and build new feature modules with confidence! 🚀
