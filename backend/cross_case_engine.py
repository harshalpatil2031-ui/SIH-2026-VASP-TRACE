"""
Cross-Case Infrastructure Correlation Engine.

Correlates transaction infrastructure (wallet addresses) across historical
investigation cases to identify recurring shared infrastructure — addresses
that appear in multiple FIR investigations.

IMPORTANT LANGUAGE GUIDANCE:
  The findings from this engine indicate shared infrastructure, historical
  wallet overlap, or recurring intermediary usage. They do NOT constitute
  automatic proof of an organized criminal syndicate. All cross-case
  correlations require analyst review before drawing investigative conclusions.

  Correct terminology: "Cross-Case Infrastructure Correlation",
    "shared infrastructure", "recurring intermediary", "historical overlap".
  Avoid: "syndicate detection", "syndicate match", "proof of organized crime".
"""
from typing import Dict, Any, List, Optional
from .models import CrossCaseAlert


class CrossCaseEngine:
    """
    Maintains an in-memory index of wallets linked to historical investigation
    cases and scans new cases for infrastructure overlaps.

    Cross-case overlaps are flagged for analyst review — they are NOT
    automatically treated as proof of coordinated criminal activity.
    """

    def __init__(self) -> None:
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

    def check_cross_case_links(
        self, current_case_id: str, nodes: List[Dict[str, Any]]
    ) -> CrossCaseAlert:
        """
        Scan all nodes in the current case against the historical infrastructure index.

        Returns a CrossCaseAlert indicating whether any shared intermediary
        addresses were found across previous investigations.  A positive result
        means shared infrastructure was detected and requires analyst review —
        it does NOT automatically indicate a criminal syndicate.
        """
        for node in nodes:
            wallet_id = node.get("id")
            if wallet_id and wallet_id in self.historical_case_index:
                history = self.historical_case_index[wallet_id]
                linked_cases = [h["case_id"] for h in history]
                linked_titles = [
                    f"{h['case_id']}: {h['title']} ({h['police_station']})"
                    for h in history
                ]
                stations = [h["police_station"] for h in history]

                return CrossCaseAlert(
                    has_shared_infrastructure=True,
                    shared_wallet_address=wallet_id,
                    linked_case_ids=linked_cases + [current_case_id],
                    linked_case_titles=linked_titles,
                    police_stations=stations,
                    # Field retained for API backward compatibility;
                    # semantically: infrastructure overlap weight, not syndicate risk
                    syndicate_risk_multiplier=2.4,
                    notes=(
                        f"CROSS-CASE INFRASTRUCTURE OVERLAP: Wallet "
                        f"{wallet_id[:10]}... was previously identified in "
                        f"{history[0]['fir_number']} by {history[0]['police_station']}. "
                        "Indicates recurring shared infrastructure across investigations. "
                        "Analyst review required before drawing investigative conclusions."
                    ),
                    analyst_review_required=True,
                )

        return CrossCaseAlert(
            has_shared_infrastructure=False,
            shared_wallet_address=None,
            linked_case_ids=[current_case_id],
            linked_case_titles=[],
            police_stations=[],
            syndicate_risk_multiplier=1.0,
            notes="No cross-case infrastructure overlap detected in the historical index.",
            analyst_review_required=False,
        )

    def register_case_nodes(
        self,
        case_id: str,
        case_meta: Dict[str, Any],
        nodes: List[Dict[str, Any]],
    ) -> None:
        """
        Register suspect and intermediary wallet addresses from a new case into
        the persistent infrastructure index.

        Only suspect and mule-typed nodes are indexed (not VASP endpoints).
        """
        for node in nodes:
            w_id = node.get("id")
            if w_id and node.get("type") in ["suspect", "mule"]:
                if w_id not in self.historical_case_index:
                    self.historical_case_index[w_id] = []
                # Avoid duplicate registration
                if not any(
                    h["case_id"] == case_id
                    for h in self.historical_case_index[w_id]
                ):
                    self.historical_case_index[w_id].append({
                        "case_id": case_id,
                        "title": case_meta.get("title", "Cyber Crime Case"),
                        "fir_number": case_meta.get("fir_number", "FIR-REG"),
                        "police_station": case_meta.get(
                            "police_station", "Cyber Cell"
                        ),
                        "date": case_meta.get("incident_date", "2026-09-01"),
                    })
