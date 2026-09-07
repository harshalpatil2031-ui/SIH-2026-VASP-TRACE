"""
Blockchain Ingestion Adapter.
Provides wallet address validation and blockchain data normalization interfaces.
"""
import re
from typing import Dict, Any, Optional


class BlockchainIngestionAdapter:
    """
    Adapter for validating and ingesting multichain wallet addresses and transaction data.
    """

    # EVM regex: 0x followed by 40 hexadecimal characters
    EVM_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")
    # TRON regex: Base58 string starting with T, length 34
    TRON_REGEX = re.compile(r"^T[1-9A-HJ-NP-za-km-z]{33}$")

    def __init__(self):
        pass

    def validate_wallet_address(self, address: str) -> Dict[str, Any]:
        """
        Validates wallet address format for supported chains (EVM, TRON, etc.).

        Returns a dictionary with 'valid' (bool), and optional 'chain' and 'message'.
        """
        if not address or not isinstance(address, str):
            return {
                "valid": False,
                "chain": None,
                "error": "Empty or invalid input format"
            }

        address = address.strip()

        if len(address) < 10:
            return {
                "valid": False,
                "chain": None,
                "error": "Address length too short"
            }

        if self.TRON_REGEX.match(address):
            return {
                "valid": True,
                "chain": "TRON",
                "normalized": address
            }

        if self.EVM_REGEX.match(address):
            return {
                "valid": True,
                "chain": "Ethereum/EVM",
                "normalized": address.lower()
            }

        return {
            "valid": False,
            "chain": "Unknown",
            "error": "Address does not match any recognized chain format"
        }
