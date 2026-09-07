"""Read-only Ethereum USDT transfer retrieval through Etherscan API V2."""
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import List
import httpx
from .blockchain_provider import BlockchainProvider

try:
    from ..models import NormalizedTransaction
except (ImportError, ValueError):
    # Support the existing flat ``backend`` test/runtime entry point.
    from models import NormalizedTransaction

class EtherscanProvider(BlockchainProvider):
    provider_name = "Etherscan API V2"
    base_url = "https://api.etherscan.io/v2/api"
    usdt_contract = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

    def __init__(self, api_key=None, timeout_seconds=20.0, max_records=100):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY", "")
        self.timeout_seconds = timeout_seconds
        self.max_records = max_records

    @property
    def is_configured(self):
        return bool(self.api_key)

    def get_downstream_transactions(self, address: str, max_hops: int = 6) -> List[NormalizedTransaction]:
        if not self.is_configured:
            raise RuntimeError("ETHERSCAN_API_KEY is not configured.")
        response = httpx.get(self.base_url, params={
            "chainid": "1", "module": "account", "action": "tokentx",
            "contractaddress": self.usdt_contract, "address": address,
            # A first-pass live investigation should prioritise the latest
            # confirmed activity.  Older history remains available through a
            # deliberate paginated evidence scan.
            "page": "1", "offset": str(self.max_records), "sort": "desc", "apikey": self.api_key,
        }, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        result = payload.get("result", [])
        if str(payload.get("status")) != "1":
            if "No transactions found" in str(result):
                return []
            raise RuntimeError("Etherscan retrieval failed: %s" % (result or payload.get("message", "unknown error")))
        retrieved_at = datetime.now(timezone.utc).isoformat()
        response_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        transfers = []
        for tx in result:
            if tx.get("from", "").lower() != address.lower():
                continue
            decimals = int(tx.get("tokenDecimal") or 0)
            amount = int(tx.get("value") or 0) / (10 ** decimals) if decimals else float(tx.get("value") or 0)
            transfers.append(NormalizedTransaction(
                tx_id=tx["hash"], from_address=tx["from"], to_address=tx["to"], amount=amount,
                token=tx.get("tokenSymbol", "USDT"),
                timestamp=datetime.fromtimestamp(int(tx["timeStamp"]), tz=timezone.utc).isoformat(),
                block_height=int(tx["blockNumber"]) if tx.get("blockNumber") else None,
                is_demo_synthetic=False, chain="Ethereum", source_provider=self.provider_name,
                retrieved_at=retrieved_at, response_sha256=response_hash,
            ))
        return transfers
