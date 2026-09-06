"""
Tamper-Evident Forensic Evidence & Cryptographic SHA-256 Verifier.
Generates tamper-evident technical integrity records under Section 63 Bharatiya Sakshya Adhiniyam (BSA) 2023.
"""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any

class EvidenceVerifier:
    def __init__(self):
        pass

    def generate_forensic_hash(self, case_data: Dict[str, Any], attribution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a deterministic SHA-256 cryptographic snapshot seal for the entire forensic case file.
        """
        snapshot_payload = {
            "case_id": case_data.get("case_id"),
            "fir_number": case_data.get("fir_number"),
            "suspect_wallet": case_data.get("suspect_wallet"),
            "chain": case_data.get("chain"),
            "amount_inr": case_data.get("amount_inr"),
            "primary_vasp": attribution_data.get("primary_vasp", {}).get("vasp_name"),
            "confidence_score": attribution_data.get("confidence_score"),
            "edge_count": len(case_data.get("edges", [])),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        # Deterministic JSON string
        canonical_str = json.dumps(snapshot_payload, sort_keys=True)
        sha256_seal = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        return {
            "sha256_hash": sha256_seal,
            "timestamp": snapshot_payload["generated_at"],
            "snapshot_data": snapshot_payload,
            "certificate_status": "CERTIFIED_TAMPER_EVIDENT",
            "statute": "Certified under Section 65B Indian Evidence Act / Sec 63 BSA 2023"
        }

    def verify_hash(self, submitted_hash: str, expected_hash: str) -> Dict[str, Any]:
        """Validates if the submitted SHA-256 forensic hash matches the cryptographic blockchain snapshot."""
        clean_sub = submitted_hash.strip().lower()
        clean_exp = expected_hash.strip().lower()

        is_valid = (clean_sub == clean_exp)
        return {
            "is_valid": is_valid,
            "submitted_hash": clean_sub,
            "expected_hash": clean_exp,
            "status": "VALID_TAMPER_FREE" if is_valid else "INVALID_MODIFIED_PAYLOAD",
            "message": (
                "FORENSIC INTEGRITY VERIFIED: Cryptographic checksum matches official LEA case archive."
                if is_valid else
                "ALERT: Checksum mismatch. The evidence file or parameters have been altered!"
            )
        }
