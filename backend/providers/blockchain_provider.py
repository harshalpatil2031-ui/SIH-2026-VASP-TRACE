"""
Abstract Blockchain Provider interface.
"""
from abc import ABC, abstractmethod
from typing import List
try:
    from ..models import NormalizedTransaction
except (ImportError, ValueError):
    from models import NormalizedTransaction

class BlockchainProvider(ABC):
    @abstractmethod
    def get_downstream_transactions(self, address: str, max_hops: int = 6) -> List[NormalizedTransaction]:
        """Fetch downstream transactions up to max_hops."""
        pass
