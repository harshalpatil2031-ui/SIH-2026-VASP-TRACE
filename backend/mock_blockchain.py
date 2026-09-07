"""
Multi-chain blockchain data simulator with simple, intuitive labels.
"""
from typing import Dict, Any, List
import hashlib
import random

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
                "tags": ["Indian Crypto Exchange", "Target for Freezing Request"],
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
                "tx_hash": "0xe6a7b8c9d0e1f2a3...",
                "timestamp": "11:18 AM",
                "hop": 1,
                "is_sweep": False,
                "notes": "Victim's money converted to 2,160 USDT sent to Middleman 1"
            },
            {
                "id": "e2-147",
                "source": "TR2x99vP8aB4c3d2e1f4a5b6c7d8e9f0a1",
                "target": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "amount": 2100.00,
                "token": "USDT",
                "tx_hash": "0x98a7b6c5d4e3f2a1...",
                "timestamp": "11:34 AM",
                "hop": 2,
                "is_sweep": False,
                "notes": "Forwarded to Mule Wallet 2 (which was also used in Mumbai Case #101)"
            },
            {
                "id": "e3-147",
                "source": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "target": "0x88cE19a456B7293E103984E29384729182937461",
                "amount": 2050.00,
                "token": "USDT",
                "tx_hash": "0x4a5b6c7d8e9f0a1b...",
                "timestamp": "11:49 AM",
                "hop": 3,
                "is_sweep": False,
                "notes": "Deposited into CoinDCX user deposit account"
            },
            {
                "id": "e4-147",
                "source": "0x88cE19a456B7293E103984E29384729182937461",
                "target": "0x72a53cDBBcc1b9efa39c834A540550e234641153",
                "amount": 2050.00,
                "token": "USDT",
                "tx_hash": "0x2c3d4e5f6a7b8c9d...",
                "timestamp": "12:05 PM",
                "hop": 4,
                "is_sweep": True,
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
                "tags": ["Binance Exchange", "Target for Freezing Request"],
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
                "tx_hash": "0x7a89b1c2...",
                "timestamp": "2:28 PM",
                "hop": 1,
                "is_sweep": False,
                "notes": "₹50,000 converted to 600 USDT sent to Middleman A"
            },
            {
                "id": "e2-101",
                "source": "0x42fE789B10c44a26E5531d054236a6FfF12389C1",
                "target": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "amount": 585.00,
                "token": "USDT",
                "tx_hash": "0x1b2c3d4e...",
                "timestamp": "2:41 PM",
                "hop": 2,
                "is_sweep": False,
                "notes": "Forwarded to Mule Wallet 2"
            },
            {
                "id": "e3-101",
                "source": "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C",
                "target": "0x39aB21f87910b87541295e86910243C78B120199",
                "amount": 580.00,
                "token": "USDT",
                "tx_hash": "0x3c4d5e6f...",
                "timestamp": "2:52 PM",
                "hop": 3,
                "is_sweep": False,
                "notes": "Sent to Binance deposit address"
            },
            {
                "id": "e4-101",
                "source": "0x39aB21f87910b87541295e86910243C78B120199",
                "target": "0x28C6c06298d514Db089934071355E5743bf21d60",
                "amount": 580.00,
                "token": "USDT",
                "tx_hash": "0x5e6f7a8b...",
                "timestamp": "3:10 PM",
                "hop": 4,
                "is_sweep": True,
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

def _generate_chain_address(seed_str: str, chain: str) -> str:
    """Generates realistic on-chain addresses based on the blockchain network."""
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    c_lower = chain.lower()
    
    if "solana" in c_lower or "sol" in c_lower:
        # Base58 charset for Solana Phantom addresses
        b58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        num = int(h, 16)
        res = []
        while num > 0 and len(res) < 44:
            res.append(b58_chars[num % 58])
            num //= 58
        return "".join(res)
    elif "tron" in c_lower:
        b58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        num = int(h, 16)
        res = ["T"]
        while num > 0 and len(res) < 34:
            res.append(b58_chars[num % 58])
            num //= 58
        return "".join(res)
    elif "bitcoin" in c_lower or "btc" in c_lower:
        return f"bc1q{h[:38]}"
    else:
        # EVM / Ethereum default
        return f"0x{h[:40]}"

def generate_custom_trace(wallet_address: str, chain: str = "Ethereum", max_hops: int = 3) -> Dict[str, Any]:
    # Auto-detect chain if needed
    if wallet_address.startswith("0x"):
        chain = "Ethereum" if chain in ["TRON", "Solana", "Bitcoin"] else chain
    elif wallet_address.startswith("T") and len(wallet_address) == 34:
        chain = "TRON"
    elif len(wallet_address) in [43, 44] and not wallet_address.startswith("0x") and not wallet_address.startswith("T"):
        chain = "Solana"
    elif wallet_address.startswith("bc1") or wallet_address.startswith("1") or wallet_address.startswith("3"):
        chain = "Bitcoin"

    token_name = "USDT (SPL)" if "solana" in chain.lower() else ("BTC" if "bitcoin" in chain.lower() else ("USDT (TRC-20)" if "tron" in chain.lower() else "USDT (ERC-20)"))

    seed_val = int(hashlib.md5(wallet_address.encode('utf-8')).hexdigest()[:8], 16)
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
        "balance": f"25 {token_name}",
        "risk_score": 95,
        "risk_level": "HIGH",
        "entity_name": f"Suspect {chain} Wallet",
        "tags": [f"{chain} Origin Wallet", "Incident Source"],
        "case_ids": ["LIVE-QUERY"],
        "is_shared": False
    })
    
    current_source = wallet_address
    total_amount = 2500.0
    current_amount = total_amount
    
    # 2. Intermediary Mule Chain (max_hops - 2 mules)
    mule_count = max(1, max_hops - 2)
    for h in range(1, mule_count + 1):
        mule_addr = _generate_chain_address(f"{wallet_address}_mule_{h}", chain)
        nodes.append({
            "id": mule_addr,
            "label": f"Intermediary Mule #{h}",
            "type": "mule",
            "chain": chain,
            "balance": f"2 {token_name}",
            "risk_score": 80,
            "risk_level": "HIGH",
            "entity_name": f"Intermediary Mule #{h}",
            "tags": [f"{chain} Mule Layer #{h}"],
            "case_ids": ["LIVE-QUERY"],
            "is_shared": False
        })
        
        tx_amt = round(current_amount * 0.96, 2)
        edges.append({
            "id": f"e_live_{h}",
            "source": current_source,
            "target": mule_addr,
            "amount": tx_amt,
            "token": token_name,
            "tx_hash": f"SIM-{hashlib.md5(f'tx_{current_source}_{mule_addr}'.encode()).hexdigest()[:8].upper()}",
            "timestamp": f"Step {h}",
            "hop": h,
            "is_sweep": False,
            "notes": f"Transfer to intermediary mule {h}"
        })
        current_source = mule_addr
        current_amount = tx_amt
        
    # 3. Exchange Deposit Address
    deposit_addr = _generate_chain_address(f"{wallet_address}_deposit", chain)
    nodes.append({
        "id": deposit_addr,
        "label": f"{selected_vasp['name']} Deposit Address",
        "type": "deposit",
        "chain": chain,
        "balance": f"0 {token_name}",
        "risk_score": 35,
        "risk_level": "MEDIUM",
        "entity_name": f"{selected_vasp['name']} User Account",
        "tags": ["Exchange Deposit Gateway", f"{chain} Inbound Gateway"],
        "case_ids": ["LIVE-QUERY"],
        "is_shared": False
    })
    
    edges.append({
        "id": "e_live_deposit",
        "source": current_source,
        "target": deposit_addr,
        "amount": round(current_amount * 0.98, 2),
        "token": token_name,
        "tx_hash": f"SIM-{hashlib.md5(f'tx_{current_source}_{deposit_addr}'.encode()).hexdigest()[:8].upper()}",
        "timestamp": "Deposit Step",
        "hop": max_hops - 1 if max_hops > 1 else 1,
        "is_sweep": False,
        "notes": f"Deposited into {selected_vasp['name']}"
    })
    
    # 4. Exchange Main Hot Wallet (At max_hops)
    vasp_hot_addr = selected_vasp["hot_wallet_patterns"][0]
    nodes.append({
        "id": vasp_hot_addr,
        "label": f"{selected_vasp['name']}",
        "type": "vasp_hot",
        "chain": chain,
        "balance": f"25M {token_name}",
        "risk_score": 10,
        "risk_level": "LOW",
        "entity_name": f"{selected_vasp['name']} Main Wallet",
        "tags": ["Identified Exchange"],
        "case_ids": ["LIVE-QUERY"],
        "is_shared": False
    })
    
    edges.append({
        "id": "e_live_hot",
        "source": deposit_addr,
        "target": vasp_hot_addr,
        "amount": round(current_amount * 0.98, 2),
        "token": token_name,
        "tx_hash": f"SIM-{hashlib.md5(f'tx_sweep_{deposit_addr}'.encode()).hexdigest()[:8].upper()}",
        "timestamp": "Consolidation",
        "hop": max_hops,
        "is_sweep": True,
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
        "notes": "Custom suspect wallet traced across blockchain to find nearest crypto exchange.",
        "nodes": nodes,
        "edges": edges,
        "selected_vasp_key": selected_vasp_key
    }
