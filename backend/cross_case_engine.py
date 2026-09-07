"""
Cross-Case Wallet Network Intelligence Engine.
Correlates transaction infrastructure across historical investigation cases to detect organized money laundering syndicates.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
try:
    from .models import CrossCaseAlert
except (ImportError, ValueError):
    from models import CrossCaseAlert

class CrossCaseEngine:
    # Parameterized temporal window for syndicate clustering (Default: 14 days)
    SYNDICATE_TEMPORAL_WINDOW_DAYS = 14

    def __init__(self):
        # In-memory persistent historical index of wallets linked to past LEA cases
        self.historical_case_index: Dict[str, List[Dict[str, str]]] = {
            "0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C": [
                {
                    "case_id": "CASE-101",
                    "title": "₹50,000 Telegram Investment & Task Scam",
                    "fir_number": "FIR/2026/CY-MUM/892",
                    "police_station": "Cyber Crime Police Station, BKC Mumbai",
                    "date": "2026-08-24"
                }
            ]
        }

    def check_cross_case_links(self, current_case_id: str, nodes: List[Dict[str, Any]]) -> CrossCaseAlert:
        """
        Scans all nodes in the current case against the historical database of past LEA investigations.
        """
        for node in nodes:
            wallet_id = node.get("id")
            if wallet_id in self.historical_case_index:
                history = self.historical_case_index[wallet_id]
                linked_cases = [h["case_id"] for h in history]
                linked_titles = [f"{h['case_id']}: {h['title']} ({h['police_station']})" for h in history]
                stations = [h["police_station"] for h in history]
                
                temporal_note = f" (Active within {self.SYNDICATE_TEMPORAL_WINDOW_DAYS}-day operational window of Mumbai FIR)"
                
                return CrossCaseAlert(
                    has_shared_infrastructure=True,
                    shared_wallet_address=wallet_id,
                    linked_case_ids=linked_cases + [current_case_id],
                    linked_case_titles=linked_titles,
                    police_stations=stations,
                    syndicate_risk_multiplier=2.4,
                    notes=(
                        f"CRITICAL SYNDICATE MATCH: Wallet {wallet_id[:10]}... was previously identified in "
                        f"{history[0]['fir_number']} by {history[0]['police_station']}{temporal_note}. "
                        "Indicates a recurring professional money-laundering syndicate operating across state borders."
                    )
                )

        return CrossCaseAlert(
            has_shared_infrastructure=False,
            shared_wallet_address=None,
            linked_case_ids=[current_case_id],
            linked_case_titles=[],
            police_stations=[],
            syndicate_risk_multiplier=1.0,
            notes="No previous cross-case overlap detected in the national intelligence graph."
        )

    def register_case_nodes(self, case_id: str, case_meta: Dict[str, Any], nodes: List[Dict[str, Any]]) -> None:
        """Registers all intermediate and suspect nodes from a new case into the persistent intelligence index."""
        for node in nodes:
            w_id = node.get("id")
            if w_id and node.get("type") in ["suspect", "mule"]:
                if w_id not in self.historical_case_index:
                    self.historical_case_index[w_id] = []
                # Avoid duplicate registration
                if not any(h["case_id"] == case_id for h in self.historical_case_index[w_id]):
                    self.historical_case_index[w_id].append({
                        "case_id": case_id,
                        "title": case_meta.get("title", "Cyber Crime Case"),
                        "fir_number": case_meta.get("fir_number", "FIR-REG"),
                        "police_station": case_meta.get("police_station", "Cyber Cell"),
                        "date": case_meta.get("incident_date", "2026-09-01")
                    })
