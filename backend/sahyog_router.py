"""
SAHYOG Protocol Adapter — Lawful VASP Requisition Generator.

Generates lawful action drafts under BNSS 2023 (Bharatiya Nagarik Suraksha
Sanhita) and routes them through the SAHYOG (I4C) law enforcement portal.

BNSS 2023 replaces the repealed CrPC 1973.  Relevant sections:
  - Section 94:  Summons to produce a document or thing.
  - Section 106: Police power to seize certain property — requires an
                 authorized investigator; this is NOT an automated account-
                 freezing mechanism.
  - Section 107: Attachment, forfeiture, and restoration of property —
                 applicable only where legally relevant; requires court order.

IMPORTANT: All outputs from this module are DRAFT suggestions only.
They require review and approval by an authorized investigator and appropriate
legal process before any action is taken.  VASPTRACE does NOT automatically
freeze accounts, seize property, or execute any legal order.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
from .models import SahyogRequest, SuggestedLawfulAction, AttributionResult


# ---------------------------------------------------------------------------
# BNSS 2023 Action Map (configurable — extend as needed)
# ---------------------------------------------------------------------------

BNSS_ACTION_MAP: Dict[str, Dict[str, str]] = {
    "KYC_DISCLOSURE": {
        "legal_reference": "BNSS 2023 Section 94",
        "title": "Summons to Produce Document / Thing",
        "description": (
            "Lawful summons requiring the VASP to produce KYC documents, "
            "account details, and identity records of the deposit wallet holder."
        ),
        "request_type": "KYC_DISCLOSURE",
        "caveat": (
            "Draft only. Must be issued by an authorized investigating officer "
            "under BNSS 2023 Section 94 following proper legal process."
        ),
    },
    "PRESERVATION_REQUEST": {
        "legal_reference": "BNSS 2023 Section 106",
        "title": "Preservation and Seizure Request",
        "description": (
            "Request for preservation and potential seizure of specified "
            "cryptocurrency assets. Requires authorized investigator action — "
            "this is NOT an automated account-freezing mechanism."
        ),
        "request_type": "PRESERVATION_REQUEST",
        "caveat": (
            "Draft only. BNSS 2023 Section 106 requires an authorized "
            "investigator to execute any seizure. No account freeze is "
            "automatically triggered by this system."
        ),
    },
    "TRANSACTION_LOGS": {
        "legal_reference": "BNSS 2023 Section 94",
        "title": "Summons for Transaction Records",
        "description": (
            "Lawful summons requiring the VASP to produce complete transaction "
            "logs, deposit/withdrawal history, and any associated IP/device records."
        ),
        "request_type": "TRANSACTION_LOGS",
        "caveat": (
            "Draft only. Must be issued by an authorized investigating officer "
            "under BNSS 2023 Section 94 following proper legal process."
        ),
    },
    "ATTACHMENT_ORDER": {
        "legal_reference": "BNSS 2023 Section 107",
        "title": "Attachment / Forfeiture Request",
        "description": (
            "Request for attachment or forfeiture of specified cryptocurrency "
            "assets under BNSS 2023 Section 107. Applicable only where legally "
            "relevant and requires a court order."
        ),
        "request_type": "ATTACHMENT_ORDER",
        "caveat": (
            "Draft only. Section 107 attachment requires a court order and "
            "is applicable only in specific legal circumstances. "
            "This system does not execute attachment automatically."
        ),
    },
}

# Confidence threshold above which a preservation request is recommended
PRESERVATION_THRESHOLD: float = 85.0


class SahyogRouter:
    """
    Generates BNSS 2023-compliant lawful requisition drafts for SAHYOG dispatch.

    All outputs are DRAFT status and require authorized investigator review.
    """

    def __init__(self) -> None:
        pass

    def generate_lawful_request(
        self,
        case_data: Dict[str, Any],
        attribution: AttributionResult,
    ) -> SahyogRequest:
        """
        Generate a lawful requisition draft based on attribution confidence.

        Args:
            case_data:   Raw case dict.
            attribution: Attribution result from AttributionEngine.

        Returns:
            SahyogRequest with DRAFT status and BNSS 2023 legal references.
        """
        case_id = case_data.get("case_id", "CASE-NEW")
        primary_vasp = attribution.primary_vasp
        conf = attribution.confidence_score

        # Select appropriate action from BNSS_ACTION_MAP
        if conf >= PRESERVATION_THRESHOLD:
            action_key = "PRESERVATION_REQUEST"
            urgency = "HIGH (Within 12 Hours) — Requires investigator approval"
        else:
            action_key = "KYC_DISCLOSURE"
            urgency = "STANDARD (Within 24 Hours) — Requires investigator approval"

        action = BNSS_ACTION_MAP[action_key]

        total_crypto = (
            f"{attribution.volume_to_vasp} {case_data.get('token', 'USDT')}"
        )
        inr_val = f"₹{case_data.get('amount_inr', 50000):,}"

        req_id = (
            f"SAHYOG-{datetime.now().strftime('%Y%m%d')}-"
            + hashlib.md5(
                f"{case_id}_{primary_vasp.vasp_name}".encode()
            ).hexdigest()[:6].upper()
        )

        suggested_action = SuggestedLawfulAction(
            legal_reference=action["legal_reference"],
            title=action["title"],
            target_vasp=primary_vasp.vasp_name,
            target_address=primary_vasp.deposit_address,
            relevant_transactions=(
                [primary_vasp.sweep_tx_hash]
                if primary_vasp.sweep_tx_hash and primary_vasp.sweep_tx_hash != "N/A"
                else []
            ),
            supporting_evidence_ref=attribution.investigation_run_id,
            request_type=action["request_type"],
            status="DRAFT — requires authorized investigator/legal process review",
            caveat=action["caveat"],
        )

        return SahyogRequest(
            request_id=req_id,
            case_id=case_id,
            vasp_name=primary_vasp.vasp_name,
            target_wallet=primary_vasp.deposit_address,
            recommended_action=action_key,
            legal_section=action["legal_reference"],
            urgency=urgency,
            fiu_nodal_officer=primary_vasp.nodal_email,
            crypto_amount=total_crypto,
            inr_equivalent=inr_val,
            status="DRAFT_READY",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            suggested_lawful_action=suggested_action,
        )

    def dispatch_sahyog_request(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulates submission of a lawful requisition draft to the SAHYOG portal.

        IMPORTANT: This is a SIMULATION only. In a production deployment,
        this would route the draft to the authorized investigator's queue on
        the I4C SAHYOG platform for human review and approval before any
        action is taken by the VASP.  No account freeze or legal action is
        automatically triggered by this system.
        """
        req_id = request_data.get("request_id", "SAHYOG-REQ")
        vasp_name = request_data.get("vasp_name", "VASP")

        receipt_hash = hashlib.sha256(
            f"{req_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()

        return {
            "request_id": req_id,
            "status": "DRAFT_SUBMITTED_FOR_REVIEW",
            "dispatch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "sahyog_receipt_token": f"0x{receipt_hash[:32]}",
            "vasp_acknowledgment": {
                "vasp": vasp_name,
                "ack_status": "DRAFT_RECEIVED_PENDING_INVESTIGATOR_APPROVAL",
                "provisional_action": (
                    "PENDING — no action taken until authorized investigator approves"
                ),
                "compliance_ticket_id": f"VASP-LEA-{receipt_hash[:8].upper()}",
            },
            "message": (
                f"Lawful requisition DRAFT submitted to {vasp_name} via SAHYOG. "
                "Status: PENDING AUTHORIZED INVESTIGATOR REVIEW. "
                "No account freeze or legal action has been automatically executed."
            ),
        }
