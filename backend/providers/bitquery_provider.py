"""Optional Bitquery GraphQL enrichment provider.

It is deliberately read-only.  Its output supplements direct chain retrieval;
it never turns an unverified label into a confirmed VASP attribution.
"""
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


class BitqueryProvider(BlockchainProvider):
    provider_name = "Bitquery GraphQL"
    endpoint = "https://streaming.bitquery.io/graphql"

    def __init__(self, api_key=None, timeout_seconds=20.0, max_records=100):
        self.api_key = api_key or os.getenv("BITQUERY_API_KEY", "")
        self.timeout_seconds = timeout_seconds
        self.max_records = max_records

    @property
    def is_configured(self):
        return bool(self.api_key)

    def get_downstream_transactions(self, address: str, max_hops: int = 6) -> List[NormalizedTransaction]:
        raise RuntimeError("Use get_downstream_transactions_for_chain with an explicit chain.")

    def get_downstream_transactions_for_chain(self, address: str, chain: str) -> List[NormalizedTransaction]:
        if not self.is_configured:
            raise RuntimeError("BITQUERY_API_KEY is not configured.")
        chain_upper = chain.upper()
        if "TRON" in chain_upper:
            query = self._tron_query()
            result_path = ("Tron", "Transfers")
        elif "ETH" in chain_upper or "EVM" in chain_upper:
            query = self._evm_query()
            result_path = ("EVM", "Transfers")
        else:
            raise RuntimeError("Bitquery live tracing currently supports TRON and Ethereum.")
        response = httpx.post(self.endpoint, json={"query": query, "variables": {"address": address, "limit": self.max_records}},
                              headers={"Authorization": "Bearer %s" % self.api_key}, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError("Bitquery retrieval failed: %s" % payload["errors"])
        records = payload.get("data", {})
        for key in result_path:
            records = records.get(key, {}) if isinstance(records, dict) else {}
        if not isinstance(records, list):
            return []
        retrieved_at = datetime.now(timezone.utc).isoformat()
        response_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        transfers = []
        for record in records:
            transfer, transaction, block = record.get("Transfer", {}), record.get("Transaction", {}), record.get("Block", {})
            sender, receiver = transfer.get("Sender", ""), transfer.get("Receiver", "")
            if sender.lower() != address.lower():
                continue
            currency = transfer.get("Currency", {})
            transfers.append(NormalizedTransaction(
                tx_id=transaction.get("Hash", ""), from_address=sender, to_address=receiver,
                amount=float(transfer.get("Amount") or 0), token=currency.get("Symbol", "USDT"),
                timestamp=transaction.get("Time") or block.get("Time") or "", block_height=block.get("Number"),
                is_demo_synthetic=False, chain="TRON" if "TRON" in chain_upper else "Ethereum",
                source_provider=self.provider_name, retrieved_at=retrieved_at, response_sha256=response_hash,
            ))
        return transfers

    def _tron_query(self):
        return '''query($address: String!, $limit: Int!) { Tron(dataset: archive) { Transfers(limit: {count: $limit}, where: {Transfer: {Sender: {is: $address}}, TransactionStatus: {Success: true}}) { Block { Number Time } Transaction { Hash Time } Transfer { Amount Sender Receiver Currency { Symbol SmartContract } } } } }'''

    def _evm_query(self):
        return '''query($address: String!, $limit: Int!) { EVM(dataset: archive, network: eth) { Transfers(limit: {count: $limit}, where: {Transfer: {Sender: {is: $address}, Currency: {SmartContract: {is: "0xdAC17F958D2ee523a2206206994597C13D831ec7"}}}}) { Block { Number Time } Transaction { Hash Time } Transfer { Amount Sender Receiver Currency { Symbol SmartContract } } } } }'''
