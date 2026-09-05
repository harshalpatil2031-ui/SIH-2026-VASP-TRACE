"""
NetworkX Graph engine for multi-hop cryptocurrency transaction graph construction and traversal.
"""
import networkx as nx
from typing import Dict, Any, List, Tuple
from .models import NodeData, EdgeData

class GraphEngine:
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

    def analyze_fund_flow(self, G: nx.DiGraph, suspect_id: str) -> Dict[str, Any]:
        """
        Analyzes multi-hop fund flow from the suspect wallet to find terminal deposit clusters and VASPs.
        """
        if suspect_id not in G:
            return {"total_hops": 0, "paths": [], "terminal_nodes": [], "volume_retained": 0.0}

        # Find all reachable nodes from suspect
        paths_to_vasp = []
        vasp_nodes = [n for n, d in G.nodes(data=True) if d.get("type") in ["deposit", "vasp_hot"]]
        
        max_hops = 0
        total_inflow = 0.0
        
        # Calculate out-degree & outbound volume from suspect
        for _, target, data in G.out_edges(suspect_id, data=True):
            total_inflow += data.get("amount", 0.0)

        for vasp_node in vasp_nodes:
            if nx.has_path(G, suspect_id, vasp_node):
                all_paths = list(nx.all_simple_paths(G, suspect_id, vasp_node))
                for p in all_paths:
                    hop_count = len(p) - 1
                    if hop_count > max_hops:
                        max_hops = hop_count
                    paths_to_vasp.append({
                        "target_node": vasp_node,
                        "path": p,
                        "hops": hop_count
                    })

        return {
            "total_hops": max_hops,
            "paths_to_vasp": paths_to_vasp,
            "total_inflow": total_inflow,
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges()
        }

    def detect_mixers_and_bridges(self, G: nx.DiGraph) -> List[Dict[str, Any]]:
        """Identifies any mixer or cross-chain bridge hops in the transaction flow."""
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
