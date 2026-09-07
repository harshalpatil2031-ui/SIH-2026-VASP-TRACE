"""
Intelligent VASP Request Router & SAHYOG Protocol Adapter v2.0.
Generates lawful Section 94, 106, and 107 BNSS 2023 requisitions and draft suggested lawful actions.

IMPORTANT CAVEAT: System output is DRAFT ONLY. No automated account freezing or asset seizure
is initiated. All actions require authorized investigator review and legal process.
"""
from typing import Dict, Any, List
from datetime import datetime
import hashlib
try:
    from .models import SahyogRequest, AttributionResult, SuggestedLawfulAction
except (ImportError, ValueError):
    from models import SahyogRequest, AttributionResult, SuggestedLawfulAction

# ─────────────────────────────────────────────────────────────────────────────
# BNSS ACTION MAP (per spec Step 1.6)
# ─────────────────────────────────────────────────────────────────────────────
BNSS_ACTION_MAP: Dict[str, Dict[str, str]] = {
    "SECTION_94": {
        "legal_reference": "Section 94 BNSS 2023",
        "title": "Summons to Produce Document or Electronic Record / Thing",
        "description": "Formal requisition to VASP Nodal Officer for KYC records, IP logs, and transaction logs.",
        "request_type": "KYC_DISCLOSURE",
        "caveat": "Requires authorized investigating officer signature."
    },
    "SECTION_106": {
        "legal_reference": "Section 106 BNSS 2023",
        "title": "Police Power to Seize Certain Property (Asset Preservation Request)",
        "description": "Request to VASP for temporary administrative preservation/hold on specified account.",
        "request_type": "FREEZE_PRESERVATION",
        "caveat": "EXPLICIT CAVEAT: Section 106 is NOT an automated account-freezing mechanism. Requires authorized investigator order and legal process."
    },
    "SECTION_107": {
        "legal_reference": "Section 107 BNSS 2023",
        "title": "Attachment, Forfeiture, or Restoration of Stolen Property",
        "description": "Formal judicial application for attachment or restoration of proceeds of crime.",
        "request_type": "JUDICIAL_ATTACHMENT",
        "caveat": "Requires judicial magistrate order under BNSS 2023 Section 107."
    }
}

class SahyogRouter:
    def __init__(self):
        self.action_map = BNSS_ACTION_MAP

    def generate_suggested_lawful_action(
        self,
        case_data: Dict[str, Any],
        attribution: AttributionResult
    ) -> SuggestedLawfulAction:
        """
        Generates a SuggestedLawfulAction object for the investigator.
        Status is strictly DRAFT.
        """
        primary_vasp = attribution.primary_vasp
        score = attribution.confidence_score
        eligible = self._is_dispatch_eligible(attribution)

        if not eligible:
            return SuggestedLawfulAction(
                legal_reference="No coercive request generated",
                title="Deep Trace & Evidence Preservation Required",
                target_vasp="Unresolved within examined evidence scope",
                target_address="",
                relevant_transactions=[],
                supporting_evidence_ref="No connected, verified VASP endpoint meets the dispatch threshold.",
                request_type="DEEP_TRACE_REQUIRED",
                status="BLOCKED — no freeze or disclosure draft may be dispatched",
                caveat="The system has not established a verified VASP endpoint within the examined hop scope. Preserve evidence and expand the investigation; do not infer ownership or initiate a freeze."
            )

        if score >= 80.0:
            action_key = "SECTION_106"
        elif score >= 40.0:
            action_key = "SECTION_94"
        else:
            action_key = "SECTION_94"

        config = self.action_map[action_key]
        tx_hashes = [c.sweep_tx_hash for c in attribution.candidates if c.sweep_tx_hash != "NONE"]

        return SuggestedLawfulAction(
            legal_reference=config["legal_reference"],
            title=config["title"],
            target_vasp=primary_vasp.vasp_name,
            target_address=primary_vasp.deposit_address,
            relevant_transactions=tx_hashes,
            supporting_evidence_ref=f"Attribution Confidence: {score}% (Rank 1)",
            request_type=config["request_type"],
            status="DRAFT — requires authorized investigator/legal process review",
            caveat=config["caveat"]
        )

    def generate_lawful_request(
        self,
        case_data: Dict[str, Any],
        attribution: AttributionResult
    ) -> SahyogRequest:
        case_id = case_data.get("case_id", "CASE-NEW")
        primary_vasp = attribution.primary_vasp
        risk_flags = getattr(attribution, "risk_flags", [])
        is_nested = "nested_service" in risk_flags
        eligible = self._is_dispatch_eligible(attribution)

        if not eligible:
            return SahyogRequest(
                request_id=f"SAHYOG-BLOCKED-{datetime.now().strftime('%Y%m%d')}",
                case_id=case_id,
                vasp_name="UNRESOLVED — NO VERIFIED VASP WITHIN EXAMINED SCOPE",
                target_wallet="",
                recommended_action="DEEP_TRACE_AND_EVIDENCE_PRESERVATION",
                legal_section="No coercive request generated by VASP TRACE",
                urgency="INVESTIGATOR REVIEW REQUIRED",
                fiu_nodal_officer="",
                crypto_amount="Not attributed",
                inr_equivalent=f"₹{case_data.get('amount_inr', 50000):,}",
                status="BLOCKED_UNRESOLVED",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
                eligible_for_dispatch=False,
                eligibility_reason="No connected, verified VASP endpoint met the 75% attribution threshold within the examined hop scope."
            )

        if attribution.confidence_score >= 80:
            if is_nested:
                rec_action = "SUB_ACCOUNT_BENEFICIAL_OWNER_FREEZE"
                legal_sec = "Section 94 (Sub-Account KYC) & Section 106 (Asset Preservation) Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 r/w PMLA 2002 & FATF Recommendation 15/16"
            else:
                rec_action = "EMERGENCY_PRESERVATION_AND_KYC"
                legal_sec = "Section 94 & Section 106 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 r/w PMLA 2002 & FATF Recommendation 15/16"
            urgency = "IMMEDIATE (Within 2 Hours)"
        else:
            rec_action = "KYC_AND_TRANSACTION_LOGS"
            legal_sec = "Section 94 Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 (Summons for Electronic Records & KYC)"
            urgency = "HIGH (Within 12 Hours)"

        total_crypto = f"{attribution.volume_to_vasp} {case_data.get('token', 'USDT')}"
        inr_val = f"₹{case_data.get('amount_inr', 50000):,}"

        req_id = f"SAHYOG-{datetime.now().strftime('%Y%m%d')}-{hashlib.md5(f'{case_id}_{primary_vasp.vasp_name}'.encode()).hexdigest()[:6].upper()}"

        return SahyogRequest(
            request_id=req_id,
            case_id=case_id,
            vasp_name=primary_vasp.vasp_name,
            target_wallet=primary_vasp.deposit_address,
            recommended_action=rec_action,
            legal_section=legal_sec,
            urgency=urgency,
            fiu_nodal_officer=primary_vasp.nodal_email or "nodal@vasp.com",
            crypto_amount=total_crypto,
            inr_equivalent=inr_val,
            status="DRAFT_READY",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            eligible_for_dispatch=True,
            eligibility_reason="Connected on-chain path, exact verified VASP address label, and attribution confidence at or above 75%; investigator and legal review remain required."
        )

    def dispatch_sahyog_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates secure API dispatch through the national SAHYOG Law Enforcement Portal."""
        if not request_data.get("eligible_for_dispatch", False):
            raise ValueError("Dispatch blocked: no connected, verified VASP endpoint met the evidence threshold. Expand the trace and obtain investigator review.")
        req_id = request_data.get("request_id", "SAHYOG-REQ")
        vasp_name = request_data.get("vasp_name", "VASP")

        receipt_hash = hashlib.sha256(f"{req_id}_{datetime.now().isoformat()}".encode()).hexdigest()

        return {
            "request_id": req_id,
            "status": "DISPATCHED_AND_ACKNOWLEDGED",
            "dispatch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "sahyog_receipt_token": f"SIM-{receipt_hash[:24].upper()}",
            "vasp_acknowledgment": {
                "vasp": vasp_name,
                "ack_status": "RECEIVED_BY_NODAL_DESK",
                "provisional_action": "DEPOSIT_ACCOUNT_PLACED_ON_72HR_HOLD",
                "compliance_ticket_id": f"VASP-LEA-{receipt_hash[:8].upper()}"
            },
            "message": f"Lawful requisition draft successfully dispatched to {vasp_name} via SAHYOG gateway under BNSS 2023."
        }

    @staticmethod
    def _is_dispatch_eligible(attribution: AttributionResult) -> bool:
        candidate = attribution.primary_vasp
        return (
            attribution.confidence_score >= 75.0
            and candidate.matched_cluster_id != "NONE"
            and bool(candidate.deposit_address)
            and candidate.vasp_name != "No qualifying VASP endpoint found within max_hops"
        )

