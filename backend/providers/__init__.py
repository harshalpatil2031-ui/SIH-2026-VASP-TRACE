"""
Blockchain provider abstraction layer for VASP TRACE.

Providers:
  - BlockchainProvider: Abstract base class (interface contract)
  - SyntheticDemoProvider: Offline demonstration mode using pre-seeded data
  - TronGridProvider: STUB ONLY — not implemented in this prototype
  - EtherscanProvider: STUB ONLY — not implemented in this prototype

All live provider stubs raise NotImplementedError with a clear message so that
the codebase cannot accidentally claim live functionality that does not exist.
"""
from .blockchain_provider import BlockchainProvider
from .synthetic_demo import SyntheticDemoProvider
from .trongrid_provider import TronGridProvider
from .etherscan_provider import EtherscanProvider

__all__ = [
    "BlockchainProvider",
    "SyntheticDemoProvider",
    "TronGridProvider",
    "EtherscanProvider",
]
