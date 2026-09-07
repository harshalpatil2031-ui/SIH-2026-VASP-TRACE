"""Bounded live-trace orchestration with explicit DEMO/LIVE/AUTO behaviour."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from time import monotonic
from threading import Lock
from typing import Any, Dict, List

try:
    from .entity_intelligence import EntityIntelligence
    from .providers import TronGridProvider, EtherscanProvider
    from .settings import settings
except (ImportError, ValueError):
    from entity_intelligence import EntityIntelligence
    from providers import TronGridProvider, EtherscanProvider
    from settings import settings


class TraceCoordinator:
    def __init__(self):
        self.entity_intel = EntityIntelligence()
        self._transfer_cache = {}
        self._cache_lock = Lock()
        self._cache_ttl_seconds = 300

    def trace_live(self, wallet: str, chain: str, max_hops: int) -> Dict[str, Any]:
        """Read confirmed outbound transfers breadth-first; no synthetic fallback here."""
        if "TRON" in chain.upper():
            primary = TronGridProvider(timeout_seconds=settings.request_timeout_seconds, max_records=settings.max_transfers_per_wallet)
        else:
            primary = EtherscanProvider(timeout_seconds=settings.request_timeout_seconds, max_records=settings.max_transfers_per_wallet)
        if not primary.is_configured:
            raise RuntimeError("Required chain provider is not configured for LIVE mode.")

        # EVM addresses are case-insensitive.  Providers commonly return them
        # lower-case, so use one canonical ID throughout the graph.  TRON
        # Base58 addresses remain case-sensitive and are left untouched.
        root_address = self._canonical_address(wallet, chain)
        nodes, edges, visited, frontier, source_events = {}, [], {root_address}, [root_address], []
        queried_wallets = 0
        started_at = monotonic()
        nodes[root_address] = self._node(root_address, chain, "suspect", "Suspect Wallet")
        for hop in range(1, min(max_hops, settings.max_hops) + 1):
            if monotonic() - started_at >= settings.max_trace_seconds:
                source_events.append({"provider": "coordinator", "status": "TIME_BUDGET_REACHED",
                                      "detail": "Returned confirmed partial graph before the live-trace time budget expired."})
                break
            remaining_budget = settings.max_wallet_queries_per_trace - queried_wallets
            addresses_to_query = frontier[:remaining_budget]
            if not addresses_to_query:
                source_events.append({"provider": "coordinator", "status": "LIMIT_REACHED",
                                      "detail": "Wallet query cap reached; trace returned partial confirmed results."})
                break
            queried_wallets += len(addresses_to_query)
            next_frontier = []
            # The direct chain provider is canonical.  Do not duplicate every
            # call with Bitquery: it doubles latency and its result is ignored
            # whenever the direct provider succeeds.
            with ThreadPoolExecutor(max_workers=min(8, len(addresses_to_query))) as pool:
                futures = {pool.submit(self._get_cached_transactions, primary, address): address
                           for address in addresses_to_query}
                grouped = {}
                for future in as_completed(futures):
                    address = futures[future]
                    try:
                        result, cache_hit = future.result()
                        grouped[address] = result
                        source_events.append({"provider": "primary_cache" if cache_hit else "primary", "address": address,
                                              "status": "SUCCESS", "records": len(result)})
                    except Exception as exc:
                        source_events.append({"provider": "primary", "address": address, "status": "FAILED", "detail": str(exc)})
            for address, transfers in grouped.items():
                # Retain the provider page as evidence in the graph, but only
                # expand the most relevant distinct recipients.  This keeps a
                # 3–4 hop trace fast while avoiding a claim of exhaustive
                # historical coverage.
                ranked_transfers = []
                for tx in transfers:
                    label = self.entity_intel.classify_address(tx.to_address)
                    ranked_transfers.append((tx, label))
                ranked_transfers.sort(key=lambda item: (bool(item[1]), item[0].amount), reverse=True)
                expanded_recipients = set()
                for tx, label in ranked_transfers:
                    source = self._canonical_address(tx.from_address, tx.chain)
                    target = self._canonical_address(tx.to_address, tx.chain)
                    key = (tx.tx_id, source, target)
                    if any(e.get("_key") == key for e in edges):
                        continue
                    node_type = "vasp_hot" if label else "mule"
                    node_label = label.label if label else "Observed Wallet"
                    nodes.setdefault(target, self._node(target, tx.chain, node_type, node_label))
                    edges.append({"id": "live-%s-%s" % (hop, len(edges) + 1), "source": source, "target": target,
                                  "amount": tx.amount, "token": tx.token, "tx_hash": tx.tx_id, "timestamp": tx.timestamp,
                                  "hop": hop, "is_sweep": bool(label), "notes": "Confirmed live transfer via %s" % tx.source_provider, "_key": key})
                    recipient = target
                    if (recipient not in visited and recipient not in expanded_recipients
                            and not label and hop < max_hops
                            and len(next_frontier) < settings.max_children_per_wallet):
                        visited.add(recipient)
                        expanded_recipients.add(recipient)
                        next_frontier.append(target)
            frontier = next_frontier
            if not frontier:
                break
        for edge in edges:
            edge.pop("_key", None)
        return {"root_address": root_address, "nodes": list(nodes.values()), "edges": edges, "source_events": source_events,
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "data_mode": "LIVE"}

    def _node(self, address, chain, node_type, label):
        return {"id": address, "label": label, "type": node_type, "chain": chain, "balance": "Not queried",
                "risk_score": 0, "risk_level": "UNASSESSED", "entity_name": label, "tags": ["LIVE ON-CHAIN DATA"],
                "case_ids": [], "is_shared": False}

    def _get_cached_transactions(self, provider, address):
        """Reuse recent provider evidence during an active investigation session."""
        key = (provider.provider_name, self._canonical_address(address, "Ethereum" if address.startswith("0x") else "TRON"))
        now = monotonic()
        with self._cache_lock:
            cached = self._transfer_cache.get(key)
            if cached and now - cached[0] < self._cache_ttl_seconds:
                return cached[1], True
        transfers = provider.get_downstream_transactions(address)
        with self._cache_lock:
            self._transfer_cache[key] = (now, transfers)
        return transfers, False

    @staticmethod
    def _canonical_address(address: str, chain: str) -> str:
        return address.lower() if "ETH" in chain.upper() or address.startswith("0x") else address
