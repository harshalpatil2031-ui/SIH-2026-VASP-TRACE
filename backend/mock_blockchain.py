"""
OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER

Pre-seeded topological transaction datasets for offline demonstration.
All transaction IDs use the SIM- prefix (e.g. SIM-A1B2C3D4) to make it
unambiguous that these are synthetic records and NOT real on-chain transactions.

This module does NOT access any live blockchain network.
All data is deterministic and for demonstration purposes only.
"""
from typing import Dict, Any, List
import hashlib
import random


def _sim_tx(seed: str) -> str:
    """Generate a clearly-synthetic, non-blockchain transaction ID."""
    return "SIM-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8].upper()


CASES_DATABASE: Dict[str, Dict[str, Any]] = {
    "CASE-147": {
        "case_id": "CASE-147",
        "title": "₹1,80,000 Loan App Extortion Case",
        "fir_number": "FIR/2026/CY-HYD/304",
        "police_station": "Cyber Crime Police Station, Cyberabad",
        "investigating_officer": "Cyber Cell Officer",
        "incident_date": "2026-08-30",
        "amount_inr": 180000,
        "chain": "TRON (USDT) / Ethereum",
        "suspect_wallet": "TJ9kLpBw81xPqrN4x78G44mX2e1Vb889Zq",
        "token": "USDT",
        "notes": "Victim was extorted by fake loan app. Stolen money converted to crypto USDT and moved across intermediary wallets to an unknown exchange.",
        "nodes": [
            {
                "id": "TJ9kLpBw81xPqrN4x78G44mX2e1Vb889Zq",
                "label": "Suspect Wallet (Stolen Funds)",
                "type": "suspect",
                "chain": "TRON",
                "balance": "85 USDT",
                "risk_score": 96,
                "risk_level": "HIGH",
                "entity_name": "Scammer Wallet",
                "tags": ["Origin of Crime", "Extortion Funds"],
                "case_ids": ["CASE-147"],
                "is_shared": False
            },
            {
                "id": "TR2x99vP8aB4c3d2e1f4a5b6c7d8e9f0a1",
                "label": "Mule Wallet 1 (Middleman)",
                "type": "mule",
                "chain": "TRON",
                "balance": "15 USDT",
                "risk_score": 85,
                "risk_level": "HIGH",
                "entity_name": "First Intermediary",
                "tags": ["Transferred 97% funds"],
                "case_ids": ["CASE-147"],
                "is_shared": False
            },
            {
                "id": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "label": "Mule Wallet 2 (Shared in Case #101!)",
                "type": "mule",
                "chain": "Ethereum",
                "balance": "2,480 USDT",
                "risk_score": 99,
                "risk_level": "CRITICAL",
                "entity_name": "Shared Mule Wallet",
                "tags": ["⚠ Also seen in Mumbai Case #101"],
                "case_ids": ["CASE-101", "CASE-147"],
                "is_shared": True
            },
            {
                "id": "0x88cE19a456B7293E103984E29384729182937461",
                "label": "Deposit Wallet (User Account at Exchange)",
                "type": "deposit",
                "chain": "Ethereum",
                "balance": "0 USDT",
                "risk_score": 30,
                "risk_level": "MEDIUM",
                "entity_name": "CoinDCX User Account",
                "tags": ["CoinDCX Deposit Address"],
                "case_ids": ["CASE-147"],
                "is_shared": False
            },
            {
                "id": "0x72a53cDBBcc1b9efa39c834A540550e234641153",
                "label": "CoinDCX (Crypto Exchange)",
                "type": "vasp_hot",
                "chain": "Ethereum",
                "balance": "18.4M USDT",
                "risk_score": 10,
                "risk_level": "LOW",
                "entity_name": "CoinDCX Exchange Main Wallet",
                "tags": ["Indian Crypto Exchange", "Target for Preservation Request"],
                "case_ids": ["CASE-147"],
                "is_shared": False
            }
        ],
        "edges": [
            {
                "id": "e1-147",
                "source": "TJ9kLpBw81xPqrN4x78G44mX2e1Vb889Zq",
                "target": "TR2x99vP8aB4c3d2e1f4a5b6c7d8e9f0a1",
                "amount": 2160.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e1-147"),
                "timestamp": "2026-08-30T11:18:00+05:30",
                "hop": 1,
                "is_sweep": False,
                "is_synthetic": True,
                "notes": "Victim's money converted to 2,160 USDT sent to Middleman 1"
            },
            {
                "id": "e2-147",
                "source": "TR2x99vP8aB4c3d2e1f4a5b6c7d8e9f0a1",
                "target": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "amount": 2100.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e2-147"),
                "timestamp": "2026-08-30T11:34:00+05:30",
                "hop": 2,
                "is_sweep": False,
                "is_synthetic": True,
                "notes": "Forwarded to Mule Wallet 2 (which was also used in Mumbai Case #101)"
            },
            {
                "id": "e3-147",
                "source": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "target": "0x88cE19a456B7293E103984E29384729182937461",
                "amount": 2050.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e3-147"),
                "timestamp": "2026-08-30T11:49:00+05:30",
                "hop": 3,
                "is_sweep": False,
                "is_synthetic": True,
                "notes": "Deposited into CoinDCX user deposit account"
            },
            {
                "id": "e4-147",
                "source": "0x88cE19a456B7293E103984E29384729182937461",
                "target": "0x72a53cDBBcc1b9efa39c834A540550e234641153",
                "amount": 2050.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e4-147"),
                "timestamp": "2026-08-30T12:05:00+05:30",
                "hop": 4,
                "is_sweep": True,
                "is_synthetic": True,
                "notes": "Automatically moved into CoinDCX exchange main custody wallet"
            }
        ]
    },
    "CASE-101": {
        "case_id": "CASE-101",
        "title": "₹50,000 Telegram Task Fraud",
        "fir_number": "FIR/2026/CY-MUM/892",
        "police_station": "Cyber Crime Police Station, Mumbai",
        "investigating_officer": "Cyber Cell Inspector",
        "incident_date": "2026-08-24",
        "amount_inr": 50000,
        "chain": "Ethereum (USDT)",
        "suspect_wallet": "0x9a3B4c28e91B33e7A41f3e76901844bF9c1E2811",
        "token": "USDT",
        "notes": "Victim cheated via fake part-time work scam. Stolen ₹50,000 sent into Binance exchange.",
        "nodes": [
            {
                "id": "0x9a3B4c28e91B33e7A41f3e76901844bF9c1E2811",
                "label": "Suspect Wallet (Crime Origin)",
                "type": "suspect",
                "chain": "Ethereum",
                "balance": "12 USDT",
                "risk_score": 98,
                "risk_level": "HIGH",
                "entity_name": "Task Scam Wallet",
                "tags": ["Telegram Fraud Origin"],
                "case_ids": ["CASE-101"],
                "is_shared": False
            },
            {
                "id": "0x42fE789B10c44a26E5531d054236a6FfF12389C1",
                "label": "Mule Wallet A (Middleman)",
                "type": "mule",
                "chain": "Ethereum",
                "balance": "0.5 USDT",
                "risk_score": 85,
                "risk_level": "HIGH",
                "entity_name": "Intermediary Mule",
                "tags": ["Middleman Account"],
                "case_ids": ["CASE-101"],
                "is_shared": False
            },
            {
                "id": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "label": "Mule Wallet 2 (Shared Mule Hub)",
                "type": "mule",
                "chain": "Ethereum",
                "balance": "840 USDT",
                "risk_score": 92,
                "risk_level": "CRITICAL",
                "entity_name": "Shared Mule Account",
                "tags": ["⚠ Also seen in Cyberabad Case #147"],
                "case_ids": ["CASE-101", "CASE-147"],
                "is_shared": True
            },
            {
                "id": "0x39aB21f87910b87541295e86910243C78B120199",
                "label": "Binance User Deposit Address",
                "type": "deposit",
                "chain": "Ethereum",
                "balance": "0 USDT",
                "risk_score": 45,
                "risk_level": "MEDIUM",
                "entity_name": "Binance User Deposit Address",
                "tags": ["Binance Account"],
                "case_ids": ["CASE-101"],
                "is_shared": False
            },
            {
                "id": "0x28C6c06298d514Db089934071355E5743bf21d60",
                "label": "Binance (Crypto Exchange)",
                "type": "vasp_hot",
                "chain": "Ethereum",
                "balance": "41.2M USDT",
                "risk_score": 10,
                "risk_level": "LOW",
                "entity_name": "Binance Main Exchange Wallet",
                "tags": ["Binance Exchange", "Target for Preservation Request"],
                "case_ids": ["CASE-101"],
                "is_shared": False
            }
        ],
        "edges": [
            {
                "id": "e1-101",
                "source": "0x9a3B4c28e91B33e7A41f3e76901844bF9c1E2811",
                "target": "0x42fE789B10c44a26E5531d054236a6FfF12389C1",
                "amount": 600.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e1-101"),
                "timestamp": "2026-08-24T14:28:00+05:30",
                "hop": 1,
                "is_sweep": False,
                "is_synthetic": True,
                "notes": "₹50,000 converted to 600 USDT sent to Middleman A"
            },
            {
                "id": "e2-101",
                "source": "0x42fE789B10c44a26E5531d054236a6FfF12389C1",
                "target": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "amount": 585.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e2-101"),
                "timestamp": "2026-08-24T14:41:00+05:30",
                "hop": 2,
                "is_sweep": False,
                "is_synthetic": True,
                "notes": "Forwarded to Mule Wallet 2"
            },
            {
                "id": "e3-101",
                "source": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "target": "0x39aB21f87910b87541295e86910243C78B120199",
                "amount": 580.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e3-101"),
                "timestamp": "2026-08-24T14:52:00+05:30",
                "hop": 3,
                "is_sweep": False,
                "is_synthetic": True,
                "notes": "Sent to Binance deposit address"
            },
            {
                "id": "e4-101",
                "source": "0x39aB21f87910b87541295e86910243C78B120199",
                "target": "0x28C6c06298d514Db089934071355E5743bf21d60",
                "amount": 580.00,
                "token": "USDT",
                "tx_hash": _sim_tx("e4-101"),
                "timestamp": "2026-08-24T15:10:00+05:30",
                "hop": 4,
                "is_sweep": True,
                "is_synthetic": True,
                "notes": "Transferred into Binance main exchange wallet"
            }
        ]
    }
}

KNOWN_VASPS = {
    "COINDCX": {
        "name": "CoinDCX Exchange",
        "jurisdiction": "India (FIU-IND Registered)",
        "fiu_ind_registered": True,
        "nodal_officer": "Chief Compliance Officer",
        "nodal_email": "lawenforcement@coindcx.com",
        "hot_wallet_patterns": ["0x72a53cDBBcc1b9efa39c834A540550e234641153"],
        "deposit_sweep_cadence": "Direct deposit to hot wallet",
        "kyc_turnaround_time": "1-2 hours"
    },
    "BINANCE": {
        "name": "Binance Exchange",
        "jurisdiction": "Global / FIU-IND Registered",
        "fiu_ind_registered": True,
        "nodal_officer": "Law Enforcement Compliance",
        "nodal_email": "compliance-in@binance.com",
        "hot_wallet_patterns": ["0x28C6c06298d514Db089934071355E5743bf21d60"],
        "deposit_sweep_cadence": "Direct deposit to hot wallet",
        "kyc_turnaround_time": "2-4 hours"
    },
    "WAZIRX": {
        "name": "WazirX Exchange",
        "jurisdiction": "India (FIU-IND Registered)",
        "fiu_ind_registered": True,
        "nodal_officer": "Legal Nodal Desk",
        "nodal_email": "nodal@wazirx.com",
        "hot_wallet_patterns": ["0x5e0b2270884ca72e934bc65e641a5015e4c44d90"],
        "deposit_sweep_cadence": "Direct deposit",
        "kyc_turnaround_time": "3-6 hours"
    }
}


def generate_custom_trace(
    wallet_address: str, chain: str = "Ethereum", max_hops: int = 3
) -> Dict[str, Any]:
    """
    Generate a deterministic synthetic trace for an arbitrary wallet address.

    OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER:
    All transactions use SIM- prefixed IDs. No live blockchain data is accessed.
    """
    seed_val = int(hashlib.md5(wallet_address.encode("utf-8")).hexdigest()[:8], 16)
    random.seed(seed_val)

    vasp_keys = list(KNOWN_VASPS.keys())
    selected_vasp_key = vasp_keys[seed_val % len(vasp_keys)]
    selected_vasp = KNOWN_VASPS[selected_vasp_key]

    nodes = []
    edges = []

    # 1. Suspect Node
    nodes.append({
        "id": wallet_address,
        "label": f"Suspect Wallet ({wallet_address[:6]}...{wallet_address[-4:]})",
        "type": "suspect",
        "chain": chain,
        "balance": "25 USDT",
        "risk_score": 95,
        "risk_level": "HIGH",
        "entity_name": "Target Suspect Address",
        "tags": ["Input Wallet Address"],
        "case_ids": ["LIVE-QUERY"],
        "is_shared": False
    })

    current_source = wallet_address
    total_amount = 2500.0
    current_amount = total_amount

    # 2. Mule Intermediaries
    for h in range(1, max_hops):
        mule_addr = "0x" + hashlib.sha256(
            f"{wallet_address}_mule_{h}".encode()
        ).hexdigest()[:40]
        nodes.append({
            "id": mule_addr,
            "label": f"Mule Wallet {h} ({mule_addr[:6]}...{mule_addr[-4:]})",
            "type": "mule",
            "chain": chain,
            "balance": "2 USDT",
            "risk_score": 80,
            "risk_level": "HIGH",
            "entity_name": f"Intermediary Mule #{h}",
            "tags": ["Middleman Wallet"],
            "case_ids": ["LIVE-QUERY"],
            "is_shared": False
        })

        tx_amt = round(current_amount * 0.96, 2)
        edge_seed = f"tx_{current_source}_{mule_addr}"
        edges.append({
            "id": f"e_live_{h}",
            "source": current_source,
            "target": mule_addr,
            "amount": tx_amt,
            "token": "USDT",
            "tx_hash": _sim_tx(edge_seed),
            "timestamp": f"2026-09-01T10:{10 + h * 12:02d}:00+05:30",
            "hop": h,
            "is_sweep": False,
            "is_synthetic": True,
            "notes": f"Transfer to intermediary mule {h}"
        })
        current_source = mule_addr
        current_amount = tx_amt

    # 3. Exchange Deposit Address
    deposit_addr = "0x" + hashlib.sha256(
        f"{wallet_address}_deposit".encode()
    ).hexdigest()[:40]
    nodes.append({
        "id": deposit_addr,
        "label": f"{selected_vasp['name']} Deposit Address",
        "type": "deposit",
        "chain": chain,
        "balance": "0 USDT",
        "risk_score": 35,
        "risk_level": "MEDIUM",
        "entity_name": f"{selected_vasp['name']} User Account",
        "tags": ["User Account at Exchange"],
        "case_ids": ["LIVE-QUERY"],
        "is_shared": False
    })

    dep_edge_seed = f"tx_{current_source}_{deposit_addr}"
    dep_amount = round(current_amount * 0.98, 2)
    edges.append({
        "id": "e_live_deposit",
        "source": current_source,
        "target": deposit_addr,
        "amount": dep_amount,
        "token": "USDT",
        "tx_hash": _sim_tx(dep_edge_seed),
        "timestamp": f"2026-09-01T10:{10 + max_hops * 12:02d}:00+05:30",
        "hop": max_hops,
        "is_sweep": False,
        "is_synthetic": True,
        "notes": f"Deposited into {selected_vasp['name']}"
    })

    # 4. Exchange Main Wallet
    vasp_hot_addr = selected_vasp["hot_wallet_patterns"][0]
    nodes.append({
        "id": vasp_hot_addr,
        "label": f"{selected_vasp['name']}",
        "type": "vasp_hot",
        "chain": chain,
        "balance": "25M USDT",
        "risk_score": 10,
        "risk_level": "LOW",
        "entity_name": f"{selected_vasp['name']} Main Wallet",
        "tags": ["Identified Exchange"],
        "case_ids": ["LIVE-QUERY"],
        "is_shared": False
    })

    sweep_edge_seed = f"tx_sweep_{deposit_addr}"
    edges.append({
        "id": "e_live_hot",
        "source": deposit_addr,
        "target": vasp_hot_addr,
        "amount": dep_amount,
        "token": "USDT",
        "tx_hash": _sim_tx(sweep_edge_seed),
        "timestamp": f"2026-09-01T10:{10 + (max_hops + 1) * 12:02d}:00+05:30",
        "hop": max_hops + 1,
        "is_sweep": True,
        "is_synthetic": True,
        "notes": "Moved into exchange main wallet"
    })

    return {
        "case_id": "LIVE-QUERY",
        "title": f"Live Trace for {wallet_address[:8]}...",
        "fir_number": "FIR/2026/LIVE-QUERY/991",
        "police_station": "Cyber Crime Investigation Unit",
        "investigating_officer": "Cyber Cell Officer",
        "incident_date": "2026-09-01",
        "amount_inr": 220000,
        "chain": chain,
        "suspect_wallet": wallet_address,
        "token": "USDT",
        "notes": "Custom suspect wallet traced across blockchain to find nearest crypto exchange. "
                 "OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER. No live blockchain data.",
        "nodes": nodes,
        "edges": edges,
        "selected_vasp_key": selected_vasp_key
    }
