"""
Intelligent VASP Request Router & SAHYOG Protocol Adapter.
Generates lawful Section 91/102 CrPC requisitions and simulates automated dispatch to VASP Nodal Officers.
"""
from typing import Dict, Any
from datetime import datetime
import hashlib
from .models import SahyogRequest, AttributionResult

class SahyogRouter:
    def __init__(self):
        pass

    def generate_lawful_request(
        self,
        case_data: Dict[str, Any],
        attribution: AttributionResult
    ) -> SahyogRequest:
        case_id = case_data.get("case_id", "CASE-NEW")
        primary_vasp = attribution.primary_vasp
        
        # Decide recommended action based on confidence
        if attribution.confidence_score >= 85:
            rec_action = "EMERGENCY_FREEZE_AND_KYC"
            legal_sec = "Section 91 & 102 of Cr.P.C. / Sec 94 & 106 BNSS 2023 r/w PMLA 2002"
            urgency = "IMMEDIATE (Within 2 Hours)"
        else:
            rec_action = "KYC_AND_TRANSACTION_LOGS"
            legal_sec = "Section 91 of Cr.P.C. / Sec 94 BNSS 2023"
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
            fiu_nodal_officer=primary_vasp.nodal_email,
            crypto_amount=total_crypto,
            inr_equivalent=inr_val,
            status="DRAFT_READY",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        )

    def dispatch_sahyog_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates automated secure API dispatch through the national SAHYOG Law Enforcement Portal."""
        req_id = request_data.get("request_id", "SAHYOG-REQ")
        vasp_name = request_data.get("vasp_name", "VASP")
        
        # Cryptographic dispatch receipt token
        receipt_hash = hashlib.sha256(f"{req_id}_{datetime.now().isoformat()}".encode()).hexdigest()

        return {
            "request_id": req_id,
            "status": "DISPATCHED_AND_ACKNOWLEDGED",
            "dispatch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "sahyog_receipt_token": f"0x{receipt_hash[:32]}",
            "vasp_acknowledgment": {
                "vasp": vasp_name,
                "ack_status": "RECEIVED_BY_NODAL_DESK",
                "provisional_action": "DEPOSIT_ACCOUNT_PLACED_ON_72HR_HOLD",
                "compliance_ticket_id": f"VASP-LEA-{receipt_hash[:8].upper()}"
            },
            "message": f"Lawful requisition successfully routed to {vasp_name} via SAHYOG secure gateway."
        }
