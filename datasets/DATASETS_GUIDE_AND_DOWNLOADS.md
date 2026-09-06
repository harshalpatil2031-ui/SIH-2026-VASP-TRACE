# 📊 Real Datasets for Cryptocurrency VASP Attribution & Forensics

This directory contains real-world datasets, ground-truth entity directories, and download instructions for forensic graph analysis in **VASP TRACE** (Problem Statement **SIH26182**).

---

## 📁 1. Included Datasets in this Project

### A. Ground-Truth VASP Directory (`datasets/known_vasp_directory.json`)
* **What it contains**: Verified hot wallets, deposit sweep patterns, and FIU-IND compliance nodal officer details for top exchanges:
  * **CoinDCX** (`0x71c8...`, `0x9A67...`, `TYDzsY...`)
  * **WazirX** (`0x5B38...`, `TWd4Wr...`)
  * **Binance** (`0x28C6...`, `TAUN6F...`, `TN3W4H...`)
  * **CoinSwitch** (`0x1111...`, `TQn9Y2...`)
  * **ZebPay** & **KuCoin**
* **Source**: Etherscan Label Cloud, Tronscan Verified Entity Tags, and FIU-IND registered entities.

---

## 🌐 2. Public Downloadable Benchmark Datasets

### A. Elliptic Dataset (MIT-IBM Watson AI Lab)
The gold standard academic dataset for graph-based cryptocurrency illicit flow detection and VASP attribution.
* **Nodes**: 203,769 Bitcoin transaction nodes
* **Edges**: 234,355 directed payment edges
* **Classes**: Licit (Exchanges, Merchants, Miners) vs. Illicit (Ransomware, Scams, Mixers, Darknet)
* **Direct Kaggle Link**: [https://www.kaggle.com/datasets/ellipticco/elliptic-data-set](https://www.kaggle.com/datasets/ellipticco/elliptic-data-set)
* **Files Included**:
  * `elliptic_txs_edgelist.csv` (Source ➔ Target directed edges)
  * `elliptic_txs_classes.csv` (1 = Illicit, 2 = Licit/Exchange, unknown)
  * `elliptic_txs_features.csv` (166 node features including timestep, in/out degrees, fees, and velocity)

---

### B. WalletExplorer Clustered Exchange Dataset
* **What it contains**: 20 Million+ Bitcoin addresses clustered using multi-input heuristics into named services (Binance, Huobi, Kraken, Poloniex, LocalBitcoins).
* **Direct Access / Download**:
  * Web Archive / Scraper: [https://www.walletexplorer.com/](https://www.walletexplorer.com/)
  * Public Dumps: Available via GitHub repository `alts-clustering/walletexplorer-dump`.

---

### C. ChainAbuse & CryptoScamDB (Reported Cybercrime Addresses)
* **What it contains**: Real suspect wallet addresses reported by cybercrime victims across fake loan apps, phishing, romance scams, and extortion.
* **Direct API / CSV Export**:
  * ChainAbuse: [https://www.chainabuse.com/](https://www.chainabuse.com/)
  * CryptoScamDB: [https://cryptoscamdb.org/](https://cryptoscamdb.org/)

---

## 🐍 3. Quick Python Script to Load & Inspect the Datasets

To load and inspect our VASP dataset in Python:

```python
import json

with open("datasets/known_vasp_directory.json", "r") as f:
    vasp_db = json.load(f)

print(f"Loaded {len(vasp_db['vasps'])} registered VASPs:")
for vasp in vasp_db["vasps"]:
    print(f"- {vasp['vasp_name']} ({vasp['country']}) -> {len(vasp['known_hot_wallets'])} Hot Wallets")
```
