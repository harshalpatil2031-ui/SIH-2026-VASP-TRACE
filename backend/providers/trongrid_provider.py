"""Read-only TRON USDT transfer retrieval through TronGrid V1."""
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

class TronGridProvider(BlockchainProvider):
    provider_name = "TronGrid V1"
    base_url = "https://api.trongrid.io/v1"
    usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

    def __init__(self, api_key=None, timeout_seconds=20.0, max_records=100):
        self.api_key = api_key or os.getenv("TRONGRID_API_KEY", "")
        self.timeout_seconds = timeout_seconds
        self.max_records = max_records

    @property
    def is_configured(self):
        return bool(self.api_key)

    def get_downstream_transactions(self, address: str, max_hops: int = 6) -> List[NormalizedTransaction]:
        if not self.is_configured:
            raise RuntimeError("TRONGRID_API_KEY is not configured.")
        response = httpx.get(
            "%s/accounts/%s/transactions/trc20" % (self.base_url, address),
            params={"only_confirmed": "true", "only_from": "true", "limit": str(min(self.max_records, 200)), "contract_address": self.usdt_contract},
            headers={"TRON-PRO-API-KEY": self.api_key}, timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        records = payload.get("data")
        if not isinstance(records, list):
            raise RuntimeError("TronGrid retrieval failed: %s" % payload.get("message", "invalid response"))
        retrieved_at = datetime.now(timezone.utc).isoformat()
        response_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        transfers = []
        for tx in records:
            if tx.get("from", "").lower() != address.lower():
                continue
            token_info = tx.get("token_info", {})
            decimals = int(token_info.get("decimals") or 6)
            if decimals == 0:
                decimals = 6
            raw_value = tx.get("value") or "0"
            amount = int(raw_value) / (10 ** decimals)
            transfers.append(NormalizedTransaction(
                tx_id=tx["transaction_id"], from_address=tx["from"], to_address=tx["to"], amount=amount,
                token=token_info.get("symbol", "USDT"),
                timestamp=datetime.fromtimestamp(int(tx["block_timestamp"]) / 1000, tz=timezone.utc).isoformat(),
                block_height=tx.get("block"), is_demo_synthetic=False, chain="TRON", source_provider=self.provider_name,
                retrieved_at=retrieved_at, response_sha256=response_hash,
            ))
        return transfers
