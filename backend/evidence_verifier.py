"""
Tamper-Evident Technical Integrity Record Generator.

Produces a SHA-256 hash over a canonicalized, immutable payload to allow
verification that investigation data has not been modified after generation.

IMPORTANT DISCLAIMERS:
  - This is a TAMPER-EVIDENT TECHNICAL INTEGRITY RECORD, not a legal certificate.
  - This does NOT constitute a Section 65B Indian Evidence Act certificate.
  - This is NOT described as "court-admissible evidence" or "legally certified".
  - The hash demonstrates technical non-modification of the recorded data fields
    and should be treated as a supporting technical record, not legal proof.

Payload Design:
  - Hashed payload: immutable investigation facts (case_id, suspect_wallet,
    chain, provider, timestamps, tx hashes, attribution summary).
  - Presentation metadata (display timestamps, UI labels) is kept OUTSIDE
    the hashed payload so cosmetic rendering changes do not invalidate the hash.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .models import EvidenceIntegrityManifest


class EvidenceVerifier:
    """
    Generates and verifies tamper-evident technical integrity records using SHA-256.
    """

    def __init__(self) -> None:
        pass

    def generate_forensic_hash(
        self,
        case_data: Dict[str, Any],
        attribution_data: Dict[str, Any],
        investigation_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a tamper-evident technical integrity record for the forensic case data.

        The canonical payload is hashed with SHA-256 using deterministic serialization
        (sorted keys, no extra whitespace).  Presentation-only fields are stored
        alongside but excluded from the hash computation.

        Args:
            case_data:             Raw case dict.
            attribution_data:      Attribution result as a dict.
            investigation_run_id:  Optional run ID for cross-referencing.

        Returns:
            Dict containing sha256_hash, timestamp, snapshot_data, and record_type.
        """
        run_id = investigation_run_id or str(uuid.uuid4())
        retrieval_ts = datetime.now(timezone.utc).isoformat()

        # Extract transaction hashes from edges (synthetic SIM- IDs or real hashes)
        tx_hashes = [
            e.get("tx_hash", "")
            for e in case_data.get("edges", [])
            if e.get("tx_hash")
        ]

        # Attribution summary (immutable facts, not display strings)
        primary_vasp = attribution_data.get("primary_vasp", {})
        attr_summary = {
            "primary_vasp_id": primary_vasp.get("vasp_id", ""),
            "primary_vasp_name": primary_vasp.get("vasp_name", ""),
            "confidence_score": attribution_data.get("confidence_score", 0.0),
            "no_qualifying_vasp": attribution_data.get("no_qualifying_vasp", False),
        }

        path_summary = (
            f"{len(case_data.get('edges', []))} hops from "
            f"{case_data.get('suspect_wallet', 'unknown')} "
            f"to {primary_vasp.get('deposit_address', 'unknown')}"
        )

        # --- HASHED PAYLOAD (immutable) ---
        hashed_payload: Dict[str, Any] = {
            "investigation_run_id": run_id,
            "case_id": case_data.get("case_id", ""),
            "suspect_wallet": case_data.get("suspect_wallet", ""),
            "chain": case_data.get("chain", ""),
            "source_provider": "OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER",
            "provider_request_id": None,
            "retrieval_timestamp_iso": retrieval_ts,
            "transaction_hashes": sorted(tx_hashes),   # Sorted for determinism
            "path_summary": path_summary,
            "attribution_result_summary": json.dumps(attr_summary, sort_keys=True),
        }

        # Deterministic serialization: sorted keys, no extra whitespace
        canonical_str = json.dumps(hashed_payload, sort_keys=True, separators=(",", ":"))
        sha256_seal = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

        # --- PRESENTATION METADATA (outside hash boundary) ---
        display_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

        manifest = EvidenceIntegrityManifest(
            investigation_run_id=run_id,
            case_id=hashed_payload["case_id"],
            suspect_wallet=hashed_payload["suspect_wallet"],
            chain=hashed_payload["chain"],
            source_provider=hashed_payload["source_provider"],
            provider_request_id=None,
            retrieval_timestamp_iso=retrieval_ts,
            transaction_hashes=sorted(tx_hashes),
            path_summary=path_summary,
            attribution_result_summary=hashed_payload["attribution_result_summary"],
            sha256_hash=sha256_seal,
            display_timestamp=display_ts,
            record_type="TAMPER_EVIDENT_TECHNICAL_INTEGRITY_RECORD",
        )

        return {
            "sha256_hash": sha256_seal,
            "timestamp": display_ts,           # Presentation only
            "snapshot_data": hashed_payload,   # Full hashed payload (for verification)
            "record_type": manifest.record_type,
            "investigation_run_id": run_id,
            # Explicitly removed:
            #   "certificate_status": "CERTIFIED_TAMPER_EVIDENT"  (misleading)
            #   "statute": "Section 65B IEA"                       (incorrect claim)
        }

    def verify_hash(
        self, submitted_hash: str, expected_hash: str
    ) -> Dict[str, Any]:
        """
        Validate a submitted SHA-256 hash against the expected integrity record hash.

        Args:
            submitted_hash: Hash string supplied by the verifier.
            expected_hash:  Hash string from the original integrity record.

        Returns:
            Dict with is_valid, status, and message.
        """
        clean_sub = submitted_hash.strip().lower()
        clean_exp = expected_hash.strip().lower()
        is_valid = clean_sub == clean_exp

        return {
            "is_valid": is_valid,
            "submitted_hash": clean_sub,
            "expected_hash": clean_exp,
            "status": "VALID_UNMODIFIED" if is_valid else "INVALID_PAYLOAD_MISMATCH",
            "message": (
                "TECHNICAL INTEGRITY VERIFIED: SHA-256 checksum matches the "
                "original tamper-evident technical integrity record. "
                "The recorded data fields have not been modified."
                if is_valid else
                "INTEGRITY CHECK FAILED: SHA-256 checksum mismatch. "
                "The evidence file or recorded parameters may have been altered."
            ),
            "record_type": "TAMPER_EVIDENT_TECHNICAL_INTEGRITY_RECORD",
            "disclaimer": (
                "This verification confirms technical non-modification of recorded "
                "data fields only. It is not a legal certificate and does not "
                "constitute a Section 65B Indian Evidence Act certificate."
            ),
        }
