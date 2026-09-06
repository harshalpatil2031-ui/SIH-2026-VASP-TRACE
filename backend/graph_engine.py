"""
Graph Engine — Multi-hop cryptocurrency transaction graph construction and traversal.

Key design decisions:
  - BFS traversal with a HARD max_hops bound enforced DURING traversal.
    Nodes beyond max_hops are NEVER added to the result set.
  - Per-path visited-set for cycle prevention (no infinite loops on circular paths).
  - (tx_hash, from, to) deduplication for duplicate transfers.
  - Zero-value transfers are traversed but flagged is_zero_value and excluded
    from flow-relevance calculations downstream.
  - The graph engine has NO knowledge of what a "VASP" is. It does not read
    or depend on the node `type` field for routing or candidate detection.
    Entity classification is the exclusive responsibility of entity_intelligence.py.
"""
import networkx as nx
from collections import deque
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field

from .models import NodeData, EdgeData


# ---------------------------------------------------------------------------
# Data structure for a single hop record (output of BFS traversal)
# ---------------------------------------------------------------------------

@dataclass
class HopRecord:
    """
    Represents a single hop in the traversal from the suspect wallet.
    Ordered list of these records is the primary output of traverse_bfs().
    """
    hop_number: int
    from_address: str
    to_address: str
    tx_hash: str
    amount: float
    token: str
    timestamp: Optional[str]
    is_zero_value: bool
    is_synthetic: bool
    edge_id: str
    path: List[str]  # Full address path from suspect to this hop's target


class GraphEngine:
    """
    Builds a directed graph from transaction data and performs BFS traversal
    to enumerate multi-hop fund flow paths.

    The graph engine is intentionally VASP-agnostic: it emits HopRecord objects
    covering all reachable addresses within max_hops, leaving VASP identification
    to the entity_intelligence layer.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Graph Construction
    # ------------------------------------------------------------------

    def build_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> nx.DiGraph:
        """
        Construct a directed NetworkX graph from node and edge dicts.

        Args:
            nodes: List of node attribute dicts (id, label, type, …)
            edges: List of edge attribute dicts (id, source, target, amount, …)

        Returns:
            A NetworkX DiGraph suitable for traversal and visualization.
        """
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node["id"], **node)
        for edge in edges:
            G.add_edge(
                edge["source"],
                edge["target"],
                id=edge.get("id", ""),
                amount=float(edge.get("amount", 0.0)),
                token=edge.get("token", ""),
                tx_hash=edge.get("tx_hash", ""),
                timestamp=edge.get("timestamp", None),
                hop=edge.get("hop", 0),
                is_sweep=edge.get("is_sweep", False),
                is_synthetic=edge.get("is_synthetic", False),
                is_zero_value=(float(edge.get("amount", 0.0)) == 0.0),
                notes=edge.get("notes", ""),
            )
        return G

    # ------------------------------------------------------------------
    # BFS Traversal (core algorithm)
    # ------------------------------------------------------------------

    def traverse_bfs(
        self,
        G: nx.DiGraph,
        start_address: str,
        max_hops: int,
    ) -> List[HopRecord]:
        """
        BFS traversal from start_address up to max_hops depth.

        Guarantees:
          - Hard max_hops bound: no node at depth > max_hops is ever added.
          - Cycle prevention: per-path visited set (not global) so that
            multi-path graphs are correctly explored without infinite loops.
          - (tx_hash, from, to) deduplication: duplicate transfers are counted
            only once regardless of how many graph paths reach them.
          - Zero-value transfers: traversed and included in hop records but
            flagged is_zero_value=True for downstream filtering.

        Args:
            G:             NetworkX DiGraph to traverse.
            start_address: Address to start BFS from (suspect wallet).
            max_hops:      Maximum hop depth. HARD bound — never exceeded.

        Returns:
            Ordered list of HopRecord objects sorted by (hop_number, timestamp).
        """
        if start_address not in G:
            return []

        hop_records: List[HopRecord] = []
        # Deduplication set: (tx_hash, from_address, to_address)
        seen_transfers: Set[Tuple[str, str, str]] = set()

        # BFS queue: (current_address, hop_depth, path_so_far, visited_in_path)
        queue: deque = deque()
        queue.append((start_address, 0, [start_address], {start_address}))

        while queue:
            current_addr, depth, path, path_visited = queue.popleft()

            if depth >= max_hops:
                # Hard bound: do not expand beyond max_hops
                continue

            for _, neighbor, edge_data in G.out_edges(current_addr, data=True):
                # Cycle prevention: skip if this neighbor is already in path
                if neighbor in path_visited:
                    continue

                tx_key = (
                    edge_data.get("tx_hash", ""),
                    current_addr,
                    neighbor,
                )
                if tx_key in seen_transfers:
                    continue
                seen_transfers.add(tx_key)

                amount = float(edge_data.get("amount", 0.0))
                new_path = path + [neighbor]
                hop_num = depth + 1

                hop_records.append(HopRecord(
                    hop_number=hop_num,
                    from_address=current_addr,
                    to_address=neighbor,
                    tx_hash=edge_data.get("tx_hash", ""),
                    amount=amount,
                    token=edge_data.get("token", ""),
                    timestamp=edge_data.get("timestamp", None),
                    is_zero_value=(amount == 0.0),
                    is_synthetic=edge_data.get("is_synthetic", False),
                    edge_id=edge_data.get("id", ""),
                    path=new_path,
                ))

                # Continue BFS from this neighbor (within max_hops)
                if hop_num < max_hops:
                    queue.append((
                        neighbor,
                        hop_num,
                        new_path,
                        path_visited | {neighbor},
                    ))

        # Sort by (hop_number, timestamp) for deterministic ordering
        hop_records.sort(key=lambda r: (r.hop_number, r.timestamp or ""))
        return hop_records

    # ------------------------------------------------------------------
    # Fund Flow Analysis (used by /api/trace pipeline)
    # ------------------------------------------------------------------

    def analyze_fund_flow(
        self,
        G: nx.DiGraph,
        suspect_id: str,
        max_hops: int = 10,
    ) -> Dict[str, Any]:
        """
        Analyze fund flow using BFS traversal.

        Note: This method is VASP-agnostic. It does NOT attempt to identify
        VASP endpoints — that is the exclusive responsibility of the attribution
        engine + entity_intelligence.

        Args:
            G:          NetworkX DiGraph.
            suspect_id: Starting wallet address.
            max_hops:   Maximum traversal depth.

        Returns:
            Dict with traversal statistics and hop records for downstream use.
        """
        if suspect_id not in G:
            return {
                "total_hops": 0,
                "paths_to_vasp": [],
                "total_inflow": 0.0,
                "node_count": G.number_of_nodes(),
                "edge_count": G.number_of_edges(),
                "hop_records": [],
            }

        hop_records = self.traverse_bfs(G, suspect_id, max_hops)

        # Total outbound volume from suspect (non-zero transfers only)
        total_inflow = sum(
            data.get("amount", 0.0)
            for _, _, data in G.out_edges(suspect_id, data=True)
            if float(data.get("amount", 0.0)) > 0
        )

        max_hop_reached = max((r.hop_number for r in hop_records), default=0)

        return {
            "total_hops": max_hop_reached,
            "paths_to_vasp": [],  # Populated by attribution engine
            "total_inflow": total_inflow,
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "hop_records": [
                {
                    "hop_number": r.hop_number,
                    "from_address": r.from_address,
                    "to_address": r.to_address,
                    "tx_hash": r.tx_hash,
                    "amount": r.amount,
                    "token": r.token,
                    "timestamp": r.timestamp,
                    "is_zero_value": r.is_zero_value,
                    "is_synthetic": r.is_synthetic,
                    "path": r.path,
                }
                for r in hop_records
            ],
        }

    # ------------------------------------------------------------------
    # Anomaly Detection (visualization aid — does NOT influence attribution)
    # ------------------------------------------------------------------

    def detect_mixers_and_bridges(self, G: nx.DiGraph) -> List[Dict[str, Any]]:
        """
        Identify any mixer or cross-chain bridge hops in the transaction flow.

        NOTE: This method reads the `type` field for visualization purposes only.
        It does NOT influence VASP attribution — entity classification for
        attribution is handled exclusively by entity_intelligence.py.
        """
        anomalies = []
        for n, d in G.nodes(data=True):
            if d.get("type") in ["mixer", "bridge"]:
                anomalies.append({
                    "node_id": n,
                    "type": d.get("type"),
                    "label": d.get("label"),
                    "risk_level": "CRITICAL",
                })
        return anomalies
