"""
Synthetic Demo Provider — VASP TRACE v2.0
Emits NormalizedTransaction objects marked as synthetic with non-hex SIM- prefixed IDs.
"""
import hashlib
from typing import List, Dict, Any
try:
    from .blockchain_provider import BlockchainProvider
except (ImportError, ValueError):
    from blockchain_provider import BlockchainProvider

try:
    from ..models import NormalizedTransaction
except (ImportError, ValueError):
    from models import NormalizedTransaction

try:
    from ..mock_blockchain import generate_custom_trace
except (ImportError, ValueError):
    from mock_blockchain import generate_custom_trace

class SyntheticDemoProvider(BlockchainProvider):
    """
    Provider implementation for offline demo mode using synthetic transaction data.
    """

    def get_downstream_transactions(self, address: str, max_hops: int = 6) -> List[NormalizedTransaction]:
        trace_data = generate_custom_trace(address)
        edges = trace_data.get("edges", [])
        
        normalized: List[NormalizedTransaction] = []
        for edge in edges:
            tx_id = edge.get("tx_hash", "")
            # Ensure SIM- prefix for synthetic IDs
            if not tx_id.startswith("SIM-"):
                raw_hash = hashlib.md5(f"{edge.get('source')}-{edge.get('target')}-{edge.get('amount')}".encode()).hexdigest()[:8]
                tx_id = f"SIM-{raw_hash.upper()}"

            normalized.append(NormalizedTransaction(
                tx_id=tx_id,
                from_address=edge.get("source", ""),
                to_address=edge.get("target", ""),
                amount=edge.get("amount", 0.0),
                token=edge.get("token", "USDT"),
                timestamp=edge.get("timestamp", ""),
                block_height=19284756,
                is_demo_synthetic=True
            ))
        return normalized
