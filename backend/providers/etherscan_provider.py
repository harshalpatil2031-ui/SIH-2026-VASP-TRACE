"""
EtherscanProvider — STUB ONLY.

This class is a placeholder for Phase 2 live Etherscan API integration.
It is NOT implemented in this prototype and will raise NotImplementedError
on all method calls.

Do NOT claim live Etherscan functionality based on the existence of this class.
"""
from typing import List, Optional
from .blockchain_provider import BlockchainProvider
from ..models import NormalizedTransaction


class EtherscanProvider(BlockchainProvider):
    """
    Stub provider for Etherscan (Ethereum blockchain) API.

    STATUS: NOT CONFIGURED FOR THIS PROTOTYPE.
    Phase 2 will implement live Etherscan REST/WebSocket integration.
    """

    PROVIDER_NAME = "Etherscan (STUB — not configured for this prototype)"

    @property
    def provider_name(self) -> str:
        return self.PROVIDER_NAME

    def get_downstream_transactions(
        self,
        address: str,
        max_hops: int,
        token: Optional[str] = None,
    ) -> List[NormalizedTransaction]:
        raise NotImplementedError(
            "EtherscanProvider is not configured for this prototype. "
            "Phase 2 will implement live Etherscan API integration. "
            "Use SyntheticDemoProvider for offline demonstration."
        )
