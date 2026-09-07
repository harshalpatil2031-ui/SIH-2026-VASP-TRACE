"""
Graph Engine v2.0 — VASP TRACE SIH26182
BFS-based multi-hop transaction traversal with hard hop enforcement,
cycle prevention, and deduplication.

The graph engine has NO knowledge of what a VASP is.
It only traverses hops and returns ordered hop records.
VASP classification is handled exclusively by entity_intelligence.py.
"""
import networkx as nx
from collections import deque
from typing import Dict, Any, List, Set, Tuple, Optional
try:
    from .models import NodeData, EdgeData
except (ImportError, ValueError):
    from models import NodeData, EdgeData

# ─────────────────────────────────────────────────────────────────────────────
# TRAVERSAL CONSTANTS (configurable)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_MAX_HOPS: int = 6          # Hard upper bound — nodes beyond this are never added
MIN_TRANSFER_AMOUNT: float = 0.0   # Zero-value transfers: traversed but flagged

class GraphEngine:
    """
    BFS graph traversal engine.
    Enforces max_hops as a hard bound DURING traversal.
    Detects and prevents cycles using a per-path visited set.
    Deduplicates transfers by (tx_hash, from, to).
    Does NOT know what a VASP is — that is entity_intelligence's job.
    """

    def __init__(self):
        pass

    def build_graph(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> nx.DiGraph:
        """Constructs a directed graph using NetworkX."""
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node["id"], **node)
        for edge in edges:
            G.add_edge(
                edge["source"],
                edge["target"],
                id=edge["id"],
                amount=edge["amount"],
                token=edge["token"],
                tx_hash=edge["tx_hash"],
                timestamp=edge["timestamp"],
                hop=edge["hop"],
                is_sweep=edge.get("is_sweep", False),
                notes=edge.get("notes", "")
            )
        return G

    def bfs_traverse(
        self,
        G: nx.DiGraph,
        start_address: str,
        max_hops: int = DEFAULT_MAX_HOPS
    ) -> List[Dict[str, Any]]:
        """
        BFS traversal from start_address up to max_hops depth.
        Returns an ordered list of hop records sorted by (hop, timestamp).

        Each hop record contains:
          hop_number, address, from_address, tx_hash, amount, token,
          timestamp, is_zero_value (flag), path (list of addresses from root)

        Guarantees:
          - Nodes beyond max_hops are NEVER added to results
          - Cycles are prevented via per-path visited set
          - Duplicate (tx_hash, from, to) transfers are skipped
        """
        if start_address not in G:
            return []

        hop_records: List[Dict[str, Any]] = []
        seen_transfers: Set[Tuple[str, str, str]] = set()  # (tx_hash, from, to) dedup

        # BFS queue: (current_address, hop_number, path_so_far)
        queue: deque = deque()
        queue.append((start_address, 0, [start_address]))

        while queue:
            current_addr, hop_num, path = queue.popleft()

            # Hard max_hops enforcement — never process beyond limit
            if hop_num >= max_hops:
                continue

            for _, neighbor, edge_data in G.out_edges(current_addr, data=True):
                next_hop = hop_num + 1

                # Hard bound: skip nodes beyond max_hops
                if next_hop > max_hops:
                    continue

                tx_hash = edge_data.get("tx_hash", "")
                amount = edge_data.get("amount", 0.0)
                token = edge_data.get("token", "")
                timestamp = edge_data.get("timestamp", "")

                # Deduplicate by (tx_hash, from, to)
                dedup_key = (tx_hash, current_addr, neighbor)
                if dedup_key in seen_transfers:
                    continue
                seen_transfers.add(dedup_key)

                # Cycle prevention: skip if neighbor already in current path
                if neighbor in path:
                    continue

                new_path = path + [neighbor]
                is_zero = (amount <= MIN_TRANSFER_AMOUNT)

                hop_records.append({
                    "hop_number": next_hop,
                    "address": neighbor,
                    "from_address": current_addr,
                    "tx_hash": tx_hash,
                    "amount": amount,
                    "token": token,
                    "timestamp": timestamp,
                    "is_zero_value": is_zero,
                    "path": new_path,
                    "notes": edge_data.get("notes", ""),
                    "is_sweep": edge_data.get("is_sweep", False)
                })

                # Continue BFS — only if under max_hops
                if next_hop < max_hops:
                    queue.append((neighbor, next_hop, new_path))

        # Sort by (hop_number, timestamp) as required by spec
        hop_records.sort(key=lambda r: (r["hop_number"], r["timestamp"]))
        return hop_records

    def analyze_fund_flow(
        self,
        G: nx.DiGraph,
        suspect_id: str,
        max_depth: int = DEFAULT_MAX_HOPS
    ) -> Dict[str, Any]:
        """
        Backward-compatible wrapper used by app.py.
        Internally uses BFS traversal.
        Returns flow analysis summary for the attribution engine.
        """
        if suspect_id not in G:
            return {
                "total_hops": 0,
                "paths_to_vasp": [],
                "total_inflow": 0.0,
                "node_count": 0,
                "edge_count": 0,
                "hop_records": []
            }

        hop_records = self.bfs_traverse(G, suspect_id, max_hops=max_depth)

        # Calculate total outbound value from suspect (non-zero only)
        total_inflow = sum(
            d.get("amount", 0.0)
            for _, _, d in G.out_edges(suspect_id, data=True)
            if d.get("amount", 0.0) > 0
        )

        max_hops_reached = max((r["hop_number"] for r in hop_records), default=0)

        return {
            "total_hops": max_hops_reached,
            "paths_to_vasp": [],   # VASP path detection moved to attribution engine
            "total_inflow": total_inflow,
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "hop_records": hop_records    # Full BFS records for attribution engine
        }

    def detect_mixers_and_bridges(self, G: nx.DiGraph) -> List[Dict[str, Any]]:
        """Identifies mixer or cross-chain bridge hops in the transaction flow."""
        anomalies = []
        for n, d in G.nodes(data=True):
            if d.get("type") in ["mixer", "bridge"]:
                anomalies.append({
                    "node_id": n,
                    "type": d.get("type"),
                    "label": d.get("label"),
                    "risk_level": "CRITICAL"
                })
        return anomalies
