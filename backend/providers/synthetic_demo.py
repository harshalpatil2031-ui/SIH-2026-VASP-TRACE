"""
SyntheticDemoProvider — OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER.

This provider uses pre-seeded deterministic data to simulate blockchain
transaction traversal without any live network calls.  Every transaction
emitted by this provider carries is_synthetic=True and uses a SIM- prefixed
transaction ID that cannot be confused with a real on-chain transaction hash.

IMPORTANT: This provider does NOT access any live blockchain.
           All data is synthetic and for demonstration purposes only.
"""
import hashlib
from typing import List, Optional, Dict, Any

from .blockchain_provider import BlockchainProvider
from ..models import NormalizedTransaction


def _sim_tx_id(seed: str) -> str:
    """
    Generate a clearly non-blockchain transaction identifier.
    Format: SIM-<8 hex chars> — unambiguous as synthetic, never a real tx hash.
    """
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"SIM-{digest[:8].upper()}"


class SyntheticDemoProvider(BlockchainProvider):
    """
    Offline demonstration provider.

    Converts pre-seeded case graph data (from mock_blockchain.CASES_DATABASE
    or generate_custom_trace) into NormalizedTransaction records with
    is_synthetic=True on every record.

    This is the ONLY provider wired in the current prototype.
    Live providers (TronGrid, Etherscan) are stub classes that raise
    NotImplementedError.
    """

    PROVIDER_NAME = "OFFLINE DEMONSTRATION MODE — SYNTHETIC LEDGER"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER_NAME

    def get_downstream_transactions(
        self,
        address: str,
        max_hops: int,
        token: Optional[str] = None,
    ) -> List[NormalizedTransaction]:
        """
        Not used directly — SyntheticDemoProvider works from pre-seeded
        case data passed via from_case_edges().  This method returns an
        empty list if called standalone (no live data source available).
        """
        return []

    def from_case_edges(
        self,
        edges: List[Dict[str, Any]],
    ) -> List[NormalizedTransaction]:
        """
        Convert raw case edge dicts (from CASES_DATABASE or generate_custom_trace)
        into NormalizedTransaction records.

        Args:
            edges: List of edge dicts with keys: id, source, target, amount,
                   token, tx_hash, timestamp, hop, is_sweep, notes.

        Returns:
            List of NormalizedTransaction, each marked is_synthetic=True with
            a SIM- prefixed tx_id.
        """
        result: List[NormalizedTransaction] = []
        for e in edges:
            amount = float(e.get("amount", 0.0))
            # Generate a deterministic SIM- id from the original edge id
            sim_id = _sim_tx_id(str(e.get("id", e.get("tx_hash", "edge"))))
            result.append(
                NormalizedTransaction(
                    tx_id=sim_id,
                    from_address=e["source"],
                    to_address=e["target"],
                    amount=amount,
                    token=e.get("token", "USDT"),
                    timestamp_iso=None,  # Demo timestamps are strings, not ISO
                    block_number=None,
                    is_synthetic=True,
                    is_zero_value=(amount == 0.0),
                    provider_request_id=None,
                    raw=e,
                )
            )
        return result
