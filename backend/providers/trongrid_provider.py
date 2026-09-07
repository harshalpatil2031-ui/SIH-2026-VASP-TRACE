"""
TronGrid Provider stub.
"""
from typing import List
try:
    from .blockchain_provider import BlockchainProvider
except (ImportError, ValueError):
    from blockchain_provider import BlockchainProvider

try:
    from ..models import NormalizedTransaction
except (ImportError, ValueError):
    from models import NormalizedTransaction

class TronGridProvider(BlockchainProvider):
    def get_downstream_transactions(self, address: str, max_hops: int = 6) -> List[NormalizedTransaction]:
        raise NotImplementedError("TronGridProvider is not configured for this prototype demonstration mode.")
