"""
Entity Intelligence Module — VASP TRACE v2.0
Classifies any blockchain address against the known VASP directory.

This is the ONLY place in the system where "is this address VASP-associated"
is decided. All other modules call this — no direct type-field reads elsewhere.

Clean interface for future Bitquery/TRONSCAN/live data integration.
"""
import json
import os
import math
from typing import Optional, Dict, Any, List
try:
    from .models import AddressLabel, EntityIntelligenceResult
except (ImportError, ValueError):
    from models import AddressLabel, EntityIntelligenceResult

# ─────────────────────────────────────────────────────────────────────────────
# LABEL STRENGTH CONSTANTS (per spec Section 1.5 — L factor)
# ─────────────────────────────────────────────────────────────────────────────
LABEL_STRENGTH_VERIFIED      = 1.00   # Exact match in known_vasp_directory.json
LABEL_STRENGTH_RECOGNIZED    = 0.75   # Recognized entity (inferred from cluster)
LABEL_STRENGTH_INFERRED      = 0.50   # Inferred cluster match
LABEL_STRENGTH_WEAK          = 0.25   # Weak/unverified

VASP_DIR_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "datasets", "known_vasp_directory.json"
)

class EntityIntelligence:
    """
    Resolves blockchain addresses to VASP entity labels.
    Reads from known_vasp_directory.json as the ground truth registry.
    Interface is designed for future live-data provider integration.
    """

    def __init__(self):
        self.vasp_directory: List[Dict[str, Any]] = self._load_vasp_directory()
        # Build a fast lookup: address -> vasp record
        self._address_index: Dict[str, Dict[str, Any]] = self._build_address_index()

    def _load_vasp_directory(self) -> List[Dict[str, Any]]:
        """Load VASP entity registry from JSON file."""
        try:
            path = os.path.abspath(VASP_DIR_PATH)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("vasps", [])
        except Exception as e:
            print(f"[EntityIntelligence] WARNING: Could not load VASP directory: {e}")
            return []

    def _build_address_index(self) -> Dict[str, Dict[str, Any]]:
        """Build a fast O(1) address -> VASP lookup index."""
        index = {}
        for vasp in self.vasp_directory:
            for wallet in vasp.get("known_hot_wallets", []):
                index[wallet.lower()] = vasp
        return index

    def classify_address(self, address: str) -> Optional[AddressLabel]:
        """
        Given any wallet address, return an AddressLabel if it is
        associated with a known VASP, or None if unknown.

        Returns None (not a candidate) for unrecognized addresses —
        the attribution engine must NEVER treat unknown addresses as VASP candidates.

        Future integration point: plug in Bitquery / TRONSCAN / live API calls here.
        """
        if not address or len(address) < 10:
            return None

        vasp = self._address_index.get(address.lower())
        if vasp:
            return AddressLabel(
                address=address,
                label=f"{vasp['vasp_name']} Hot Wallet",
                vasp_id=vasp["vasp_id"],
                vasp_name=vasp["vasp_name"],
                entity_type="vasp_hot",
                confidence=LABEL_STRENGTH_VERIFIED
            )
        return None   # Unknown address — not a VASP candidate

    def resolve_graph_nodes(self, nodes: List[Dict[str, Any]]) -> EntityIntelligenceResult:
        """
        Scan all graph nodes and resolve VASP labels.
        Returns the first matched VASP and all address labels found.
        Called by the attribution engine instead of reading type fields directly.
        """
        labels: List[AddressLabel] = []
        first_match: Optional[AddressLabel] = None
        deposit_address: Optional[str] = None
        vasp_hot_address: Optional[str] = None

        for node in nodes:
            addr = node.get("id", "")
            label = self.classify_address(addr)
            if label:
                labels.append(label)
                if first_match is None:
                    first_match = label
                    # Set deposit/hot wallet addresses
                    deposit_address = addr
                    vasp_hot_address = addr

        if first_match:
            vasp_info = self._address_index.get(first_match.address.lower(), {})
            return EntityIntelligenceResult(
                vasp_matched=True,
                matched_vasp_id=first_match.vasp_id,
                matched_vasp_name=first_match.vasp_name,
                matched_vasp_info=vasp_info,
                deposit_address=deposit_address,
                vasp_hot_address=vasp_hot_address,
                address_labels=labels,
                jurisdiction=vasp_info.get("country", "Unknown"),
                fiu_ind_registered=vasp_info.get("fiu_ind_registered", False),
                nodal_email=vasp_info.get("compliance_nodal_email", "")
            )

        return EntityIntelligenceResult(
            vasp_matched=False,
            address_labels=labels
        )

    def get_vasp_info(self, vasp_id: str) -> Optional[Dict[str, Any]]:
        """Look up full VASP info by vasp_id (e.g. 'VASP-COINDCX')."""
        for vasp in self.vasp_directory:
            if vasp.get("vasp_id") == vasp_id:
                return vasp
        return None

    def get_label_strength(self, label: AddressLabel) -> float:
        """Return the L-factor label strength for scoring."""
        return label.confidence  # Already set during classify_address

    def get_vasp_count(self) -> int:
        """Total number of VASPs in the registry."""
        return len(self.vasp_directory)

    def get_all_vasp_names(self) -> List[str]:
        """List of all known VASP names."""
        return [v["vasp_name"] for v in self.vasp_directory]
