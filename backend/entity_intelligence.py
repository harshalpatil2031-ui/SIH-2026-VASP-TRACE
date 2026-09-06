"""
Entity Intelligence — VASP Address Registry Lookup.

This is the SINGLE authoritative source for determining whether a blockchain
address is associated with a known VASP entity. No other module may make
"is this a VASP address?" decisions independently.

Current data source: known_vasp_directory.json (curated registry + demo seed addresses).

Integration point for live sources (Phase 2):
  - Bitquery GraphQL API (cluster labels, entity tags)
  - TRONSCAN Verified Exchange Tags
  - WalletExplorer Clustered Entities
  - Etherscan Labeled Cloud Directory
  When live sources are integrated, each must be mapped to a distinct
  `source` value in AddressLabel so that independent_sources is counted
  correctly and regulatory registration (FIU-IND) is NEVER conflated with
  address-level evidence.

IMPORTANT: A VASP's regulatory registration (e.g. FIU-IND listing) is NOT
treated as proof that a specific address belongs to that VASP.  Only a direct
address-level label from an independent source constitutes evidence.
"""
import json
import os
from typing import List, Dict, Optional
from .models import AddressLabel

# ---------------------------------------------------------------------------
# Path to the VASP entity registry
# ---------------------------------------------------------------------------
_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "datasets",
    "known_vasp_directory.json",
)


class EntityIntelligence:
    """
    Resolves blockchain addresses to AddressLabel records using the
    known_vasp_directory.json registry.

    Singleton-style usage: instantiate once and reuse across the application.

    Future Integration Point:
      Override or extend `get_labels()` to query live APIs (Bitquery,
      TRONSCAN, Etherscan) and merge results, setting independent_sources
      to reflect the actual number of distinct sources that confirmed the label.
    """

    def __init__(self, registry_path: str = _REGISTRY_PATH) -> None:
        """
        Load the VASP entity registry from disk.

        Args:
            registry_path: Path to known_vasp_directory.json.
                           Defaults to the project datasets directory.
        """
        self._address_map: Dict[str, List[AddressLabel]] = {}
        self._vasp_hot_wallets: Dict[str, List[str]] = {}  # vasp_id -> [addresses]
        self._load_registry(registry_path)

    def _load_registry(self, path: str) -> None:
        """Parse known_vasp_directory.json and build the address lookup index."""
        if not os.path.exists(path):
            return  # Graceful degradation — no labels available

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        for vasp in data.get("vasps", []):
            vasp_id = vasp["vasp_id"]
            vasp_name = vasp["vasp_name"]
            jurisdiction = vasp.get("country", "Unknown")
            fiu_registered = vasp.get("fiu_ind_registered", False)
            nodal_email = vasp.get("compliance_nodal_email", "")
            hot_wallets = vasp.get("known_hot_wallets", [])

            self._vasp_hot_wallets[vasp_id] = hot_wallets

            for address in hot_wallets:
                label = AddressLabel(
                    address=address,
                    vasp_id=vasp_id,
                    vasp_name=vasp_name,
                    label_type="hot_wallet",
                    # Known hot wallets from the curated directory are "recognized entity"
                    # strength — strong enough for attribution but requires independent
                    # address-level confirmation for the I (independent corroboration) factor.
                    strength="recognized",
                    source="VASP_DIRECTORY",
                    jurisdiction=jurisdiction,
                    fiu_ind_registered=fiu_registered,
                    nodal_email=nodal_email,
                    independent_sources=1,
                )
                if address not in self._address_map:
                    self._address_map[address] = []
                self._address_map[address].append(label)

    def get_labels(self, address: str) -> List[AddressLabel]:
        """
        Return all known AddressLabel records for *address*.

        Returns an empty list if the address has no known VASP association —
        the caller must handle the unlabeled case gracefully.

        Future Integration Point:
          Insert live API calls here (Bitquery, TRONSCAN) and merge results
          into the returned list, incrementing independent_sources per distinct
          confirmed source.
        """
        return list(self._address_map.get(address, []))

    def get_vasp_hot_wallets(self, vasp_id: str) -> List[str]:
        """
        Return all known hot wallet addresses for a given vasp_id.
        Used by the attribution engine to check sweep evidence (factor S).
        """
        return list(self._vasp_hot_wallets.get(vasp_id, []))

    def is_vasp_address(self, address: str) -> bool:
        """Convenience method: True if address has at least one label."""
        return bool(self._address_map.get(address))

    def get_all_vasp_ids(self) -> List[str]:
        """Return all VASP IDs in the registry."""
        return list(self._vasp_hot_wallets.keys())

    def get_label_strength_score(self, strength: str) -> float:
        """
        Map label strength string to normalized [0, 1] score for factor L.

        Strength tiers:
          verified    → 1.0   (multi-source, authoritative confirmation)
          recognized  → 0.75  (known entity in curated registry)
          inferred    → 0.5   (cluster inference, not directly confirmed)
          weak        → 0.25  (unverified, single-source hint)
        """
        _MAP = {
            "verified": 1.0,
            "recognized": 0.75,
            "inferred": 0.5,
            "weak": 0.25,
        }
        return _MAP.get(strength, 0.25)
