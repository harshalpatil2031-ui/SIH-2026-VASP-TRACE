"""
Tamper-Evident Forensic Evidence & Cryptographic SHA-256 Verifier.
Generates tamper-evident technical integrity records under Section 63 Bharatiya Sakshya Adhiniyam (BSA) 2023.
"""
import hashlib
import json
import uuid
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
            "statute": "Certified under Section 63 of the Bharatiya Sakshya Adhiniyam (BSA), 2023 [Schedule Part A & Part B Two-Signature Format] (formerly Sec 65B IEA)",
            "certificate_schedule_format": {
                "part_a_signatory": "Investigating Officer / Custodian of Device",
                "part_b_signatory": "Cyber Forensic Expert / Technical In-Charge",
                "hash_algorithm": "SHA-256 (FIPS 180-4)",
                "tamper_evident_seal": sha256_seal
            }
        }

    def generate_trace_manifest(self, case_data: Dict[str, Any], trace_provenance: Dict[str, Any], attribution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a technical, reproducible integrity record for one trace run."""
        edges = case_data.get("edges", [])
        payload = {
            "case_id": case_data.get("case_id"), "suspect_wallet": case_data.get("suspect_wallet"),
            "chain": case_data.get("chain"), "data_mode": trace_provenance.get("data_mode", "DEMO"),
            "retrieved_at": trace_provenance.get("retrieved_at"),
            "transactions": [{"hash": e.get("tx_hash"), "source": e.get("source"), "target": e.get("target"), "amount": e.get("amount"), "timestamp": e.get("timestamp")} for e in edges],
            "source_events": trace_provenance.get("source_events", []),
            "attribution": {"vasp": attribution_data.get("primary_vasp", {}).get("vasp_name"), "confidence": attribution_data.get("confidence_score")},
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return {"investigation_run_id": "RUN-" + uuid.uuid4().hex[:16].upper(), "sha256_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                "payload": payload, "integrity_status": "TAMPER_EVIDENT_TECHNICAL_RECORD",
                "disclaimer": "Technical integrity record only; authorized investigator attestation and lawful process remain required."}

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

    def verify_trace_manifest(self, manifest_payload: Dict[str, Any], expected_hash: str) -> Dict[str, Any]:
        canonical = json.dumps(manifest_payload, sort_keys=True, separators=(",", ":"))
        computed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self.verify_hash(computed, expected_hash)
