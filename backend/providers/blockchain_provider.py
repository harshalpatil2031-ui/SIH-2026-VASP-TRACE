"""
Abstract base class for all blockchain data providers.
"""
from abc import ABC, abstractmethod
from typing import List
from ..models import NormalizedTransaction


class BlockchainProvider(ABC):
    """
    Interface contract for all blockchain data providers.

    Implementations must emit NormalizedTransaction objects so that the
    graph engine and attribution engine are fully provider-agnostic.

    Concrete implementations:
      - SyntheticDemoProvider (offline demo)
      - TronGridProvider (stub — Phase 2)
      - EtherscanProvider (stub — Phase 2)
    """

    @abstractmethod
    def get_downstream_transactions(
        self,
        address: str,
        max_hops: int,
        token: Optional[str] = None,
    ) -> List[NormalizedTransaction]:
        """
        Retrieve all downstream transactions from *address* up to *max_hops*
        hops depth.

        Args:
            address:  Starting wallet address.
            max_hops: Maximum traversal depth. Implementations MUST honour
                      this bound — no nodes beyond max_hops may be included.
            token:    Optional token filter (e.g. "USDT"). None = all tokens.

        Returns:
            A list of NormalizedTransaction records in no guaranteed order.
            The graph engine will re-sort and deduplicate.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (used in Evidence Manifest)."""
        ...


# Allow Optional import without circular issues
from typing import Optional
