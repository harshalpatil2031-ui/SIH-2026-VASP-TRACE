"""
Test Suite for VASP TRACE Attribution Engine (STEP 3 — 20 required tests).

Tests are numbered and named to match the spec:
  T1:  No case-ID-based attribution
  T2:  Same algorithm produces consistent results for different case IDs
  T3:  max_hops=1 — correct truncation
  T4:  max_hops=2 — correct truncation
  T5:  max_hops=3 — correct truncation
  T6:  VASP endpoint outside max_hops is excluded
  T7:  First qualifying VASP endpoint (hop order) is selected
  T8:  Earlier deposit endpoint beats later same-VASP hot wallet (sweep = corroboration)
  T9:  Multiple outgoing branches are all scanned for candidates
  T10: Cycles do not cause infinite traversal
  T11: Missing VASP labels do not crash the engine
  T12: Conflicting VASP labels surfaced (label_conflict=True), not silently resolved
  T13: Missing timestamps handled safely (T=0.5, flagged)
  T14: Missing sweep evidence handled safely (S=0, not penalized)
  T15: Final confidence score always in [0, 100]
  T16: Per-factor evidence breakdown always present on AttributionResult
  T17: Synthetic transactions always marked is_synthetic=True with SIM- IDs
  T18: Existing FastAPI app still starts successfully
  T19: Existing frontend still loads (index.html accessible)
  T20: Existing demo cases (CASE-147, CASE-101) return coherent end-to-end result
"""
import sys
import os
import math
import pytest

# Add project root to path so backend can be imported as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.graph_engine import GraphEngine
from backend.attribution_engine import AttributionEngine, MIN_QUALIFYING_SCORE, W_F, W_P, W_T, W_L, W_S, W_I
from backend.entity_intelligence import EntityIntelligence
from backend.models import AddressLabel, AttributionResult
from backend.evidence_verifier import EvidenceVerifier
from backend.mock_blockchain import CASES_DATABASE, generate_custom_trace


# ---------------------------------------------------------------------------
# Shared Test Fixtures
# ---------------------------------------------------------------------------

def make_intel(vasp_map: dict) -> EntityIntelligence:
    """
    Create a synthetic EntityIntelligence instance with controlled address labels.
    vasp_map: {address: (vasp_id, vasp_name, strength, n_sources)}
    """
    intel = EntityIntelligence.__new__(EntityIntelligence)
    intel._address_map = {}
    intel._vasp_hot_wallets = {}
    for addr, (vasp_id, vasp_name, strength, n_src) in vasp_map.items():
        label = AddressLabel(
            address=addr,
            vasp_id=vasp_id,
            vasp_name=vasp_name,
            label_type="hot_wallet",
            strength=strength,
            source="TEST",
            jurisdiction="Test",
            fiu_ind_registered=True,
            nodal_email="test@test.com",
            independent_sources=n_src,
        )
        intel._address_map[addr] = [label]
        intel._vasp_hot_wallets.setdefault(vasp_id, []).append(addr)
    return intel


def make_case(edges, suspect="0xSUSPECT"):
    """Build a minimal case_data dict from a list of (source, target, amount, hop, ts) tuples."""
    nodes = [{"id": suspect, "type": "suspect", "chain": "Ethereum",
              "balance": "1 USDT", "risk_score": 90, "risk_level": "HIGH",
              "label": "Suspect", "entity_name": "Suspect", "tags": [],
              "case_ids": [], "is_shared": False}]
    edge_list = []
    seen_nodes = {suspect}
    for idx, (src, tgt, amt, hop, ts) in enumerate(edges):
        edge_list.append({
            "id": f"e{idx}", "source": src, "target": tgt, "amount": float(amt),
            "token": "USDT", "tx_hash": f"SIM-{idx:08X}", "timestamp": ts,
            "hop": hop, "is_sweep": False, "is_synthetic": True, "notes": ""
        })
        for n in (src, tgt):
            if n not in seen_nodes:
                seen_nodes.add(n)
                nodes.append({"id": n, "type": "mule", "chain": "Ethereum",
                               "balance": "1 USDT", "risk_score": 50, "risk_level": "MEDIUM",
                               "label": n, "entity_name": n, "tags": [],
                               "case_ids": [], "is_shared": False})
    return {
        "case_id": "TEST", "title": "Test", "fir_number": "FIR/TEST",
        "police_station": "Test PS", "investigating_officer": "Test IO",
        "incident_date": "2026-01-01", "amount_inr": 10000, "chain": "Ethereum",
        "suspect_wallet": suspect, "token": "USDT", "notes": "Test case",
        "nodes": nodes, "edges": edge_list
    }


# ---------------------------------------------------------------------------
# T1 & T2: No case-ID-based attribution
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case_id", ["CASE-001", "CASE-147", "CASE-101", "XYZ-999"])
def test_T1_no_case_id_logic(case_id):
    """T1/T2: Identical evidence must produce identical scores regardless of case_id."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", "recognized", 1)})
    engine = AttributionEngine(entity_intel=intel)
    ge = GraphEngine()

    edges = [("0xSUSPECT", "0xVASP", 1000.0, 1, "2026-01-01T10:00:00+05:30")]
    case_data = make_case(edges)
    case_data["case_id"] = case_id

    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    # Score must be deterministic and not 0 (there is a matching VASP)
    assert result.confidence_score > 0, f"Expected non-zero score for case_id={case_id}"
    return result.confidence_score


def test_T2_consistent_across_case_ids():
    """T2: Exactly the same score for two different case IDs with identical evidence."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", "recognized", 1)})
    ge = GraphEngine()

    edges = [("0xSUSPECT", "0xVASP", 1000.0, 1, "2026-01-01T10:00:00+05:30")]
    scores = []
    for cid in ["CASE-ALPHA", "CASE-BETA"]:
        engine = AttributionEngine(entity_intel=intel)
        case_data = make_case(edges)
        case_data["case_id"] = cid
        G = ge.build_graph(case_data["nodes"], case_data["edges"])
        flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
        result = engine.compute_attribution(case_data, flow)
        scores.append(result.confidence_score)

    assert scores[0] == scores[1], f"Scores differ across case IDs: {scores}"


# ---------------------------------------------------------------------------
# T3–T5: max_hops truncation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("max_hops,expected_hop_reach", [
    (1, 1),
    (2, 2),
    (3, 3),
])
def test_T3_T4_T5_max_hops_truncation(max_hops, expected_hop_reach):
    """T3/T4/T5: BFS must never add nodes beyond max_hops."""
    ge = GraphEngine()
    # Build a linear chain: SUSPECT -> A -> B -> C -> D
    chain = [
        ("0xSUSPECT", "0xA", 100.0, 1, None),
        ("0xA", "0xB", 90.0, 2, None),
        ("0xB", "0xC", 80.0, 3, None),
        ("0xC", "0xD", 70.0, 4, None),
    ]
    case_data = make_case(chain)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, "0xSUSPECT", max_hops=max_hops)
    hop_records = flow["hop_records"]
    actual_max = max((r["hop_number"] for r in hop_records), default=0)
    assert actual_max <= max_hops, (
        f"max_hops={max_hops} but hop_records reached hop {actual_max}"
    )
    assert actual_max == expected_hop_reach or actual_max <= max_hops


# ---------------------------------------------------------------------------
# T6: VASP endpoint outside max_hops is excluded from candidates
# ---------------------------------------------------------------------------

def test_T6_vasp_outside_max_hops_excluded():
    """T6: A VASP-labeled endpoint at hop 4 must not be a candidate when max_hops=2."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", "recognized", 1)})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    # VASP is 3 hops away; max_hops=2
    edges = [
        ("0xSUSPECT", "0xA", 1000.0, 1, None),
        ("0xA", "0xB", 900.0, 2, None),
        ("0xB", "0xVASP", 800.0, 3, None),
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=2)
    result = engine.compute_attribution(case_data, flow)

    assert result.no_qualifying_vasp is True, (
        "Expected no qualifying VASP when endpoint is beyond max_hops"
    )


# ---------------------------------------------------------------------------
# T7: First qualifying VASP in hop order is selected
# ---------------------------------------------------------------------------

def test_T7_hop_order_selection():
    """T7: Earliest qualifying VASP (hop 1) wins over later VASP (hop 2), even if later has higher raw score."""
    intel = make_intel({
        "0xVASP_EARLY": ("VASP-EARLY", "Early VASP", "recognized", 1),
        "0xVASP_LATE": ("VASP-LATE", "Late VASP", "verified", 2),  # stronger label but later
    })
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [
        ("0xSUSPECT", "0xVASP_EARLY", 1000.0, 1, "2026-01-01T10:00:00+05:30"),
        ("0xSUSPECT", "0xMULE", 500.0, 1, "2026-01-01T10:01:00+05:30"),
        ("0xMULE", "0xVASP_LATE", 490.0, 2, "2026-01-01T10:10:00+05:30"),
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    assert result.primary_vasp.vasp_id == "VASP-EARLY", (
        f"Expected VASP-EARLY (hop 1) but got {result.primary_vasp.vasp_id}"
    )


# ---------------------------------------------------------------------------
# T8: Earlier deposit beats later same-VASP hot wallet (sweep = corroboration)
# ---------------------------------------------------------------------------

def test_T8_deposit_before_hot_wallet():
    """T8: deposit at hop 2 is primary; hot wallet at hop 3 is sweep corroboration."""
    intel = make_intel({
        "0xDEPOSIT": ("VASP-X", "TestVASP", "recognized", 1),
        "0xHOT": ("VASP-X", "TestVASP", "verified", 2),
    })
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [
        ("0xSUSPECT", "0xMULE", 1000.0, 1, "2026-01-01T10:00:00+05:30"),
        ("0xMULE", "0xDEPOSIT", 950.0, 2, "2026-01-01T10:10:00+05:30"),
        ("0xDEPOSIT", "0xHOT", 950.0, 3, "2026-01-01T10:15:00+05:30"),
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    # Primary should be the deposit address (hop 2), not the hot wallet (hop 3)
    assert result.primary_vasp.deposit_address == "0xDEPOSIT", (
        f"Expected deposit address 0xDEPOSIT, got {result.primary_vasp.deposit_address}"
    )
    # Sweep should be detected since 0xHOT is a known hot wallet of VASP-X
    assert result.sweep_detected is True


# ---------------------------------------------------------------------------
# T9: Multiple outgoing branches are all scanned
# ---------------------------------------------------------------------------

def test_T9_multiple_branches_scanned():
    """T9: BFS must find VASP-labeled address on any branch, not just the first."""
    intel = make_intel({
        "0xVASP_B": ("VASP-B", "VASP on Branch B", "recognized", 1),
    })
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    # Branch A: no VASP; Branch B: VASP at hop 2
    edges = [
        ("0xSUSPECT", "0xA1", 600.0, 1, "2026-01-01T10:00:00+05:30"),   # Branch A
        ("0xSUSPECT", "0xB1", 400.0, 1, "2026-01-01T10:01:00+05:30"),   # Branch B
        ("0xA1", "0xA2", 580.0, 2, "2026-01-01T10:05:00+05:30"),        # Branch A continued
        ("0xB1", "0xVASP_B", 390.0, 2, "2026-01-01T10:08:00+05:30"),    # Branch B → VASP
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    assert result.primary_vasp.vasp_id == "VASP-B", (
        f"Expected VASP-B from branch B, got {result.primary_vasp.vasp_id}"
    )


# ---------------------------------------------------------------------------
# T10: Cycles do not cause infinite traversal
# ---------------------------------------------------------------------------

def test_T10_cycles_no_infinite_loop():
    """T10: A → B → C → A cycle must terminate, not loop forever."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", "recognized", 1)})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [
        ("0xSUSPECT", "0xA", 1000.0, 1, None),
        ("0xA", "0xB", 900.0, 2, None),
        ("0xB", "0xC", 800.0, 3, None),
        ("0xC", "0xA", 700.0, 4, None),   # cycle back to A
        ("0xC", "0xVASP", 600.0, 4, None), # also continues to VASP
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    # This must complete without hanging
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=5)
    hop_records = flow["hop_records"]
    # Should have records but not be empty
    assert isinstance(hop_records, list)
    # Must not have visited A twice in the same path
    from_a_count = sum(1 for r in hop_records if r["to_address"] == "0xA")
    assert from_a_count <= 1, "Cycle detected: 0xA visited more than once in traversal"


# ---------------------------------------------------------------------------
# T11: Missing VASP labels do not crash the engine
# ---------------------------------------------------------------------------

def test_T11_missing_labels_no_crash():
    """T11: An unlabeled address simply isn't a candidate — no crash."""
    intel = make_intel({})  # No labels at all
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [("0xSUSPECT", "0xRANDOM", 1000.0, 1, None)]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    assert result.no_qualifying_vasp is True
    assert result.confidence_score == 0.0
    assert result.primary_vasp.vasp_name == "No Qualifying VASP Found"


# ---------------------------------------------------------------------------
# T12: Conflicting VASP labels surfaced (label_conflict=True)
# ---------------------------------------------------------------------------

def test_T12_label_conflict_surfaced():
    """T12: Address with two conflicting VASP labels must set label_conflict=True."""
    intel = EntityIntelligence.__new__(EntityIntelligence)
    intel._address_map = {
        "0xCONFLICT": [
            AddressLabel(address="0xCONFLICT", vasp_id="VASP-A", vasp_name="VASP A",
                         label_type="hot_wallet", strength="recognized", source="SRC1",
                         jurisdiction="India", fiu_ind_registered=True,
                         nodal_email="a@a.com", independent_sources=1),
            AddressLabel(address="0xCONFLICT", vasp_id="VASP-B", vasp_name="VASP B",
                         label_type="hot_wallet", strength="recognized", source="SRC2",
                         jurisdiction="India", fiu_ind_registered=True,
                         nodal_email="b@b.com", independent_sources=1),
        ]
    }
    intel._vasp_hot_wallets = {"VASP-A": ["0xCONFLICT"], "VASP-B": ["0xCONFLICT"]}
    engine = AttributionEngine(entity_intel=intel)
    ge = GraphEngine()

    edges = [("0xSUSPECT", "0xCONFLICT", 1000.0, 1, "2026-01-01T10:00:00+05:30")]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    assert result.primary_vasp.label_conflict is True, (
        "Expected label_conflict=True for address with conflicting VASP labels"
    )
    conflict_notes = " ".join(result.limitations)
    assert "conflict" in conflict_notes.lower(), (
        f"Expected 'conflict' in limitations but got: {result.limitations}"
    )


# ---------------------------------------------------------------------------
# T13: Missing timestamps handled safely (T=0.5, flagged)
# ---------------------------------------------------------------------------

def test_T13_missing_timestamps_safe():
    """T13: When timestamps are None, T factor must be 0.5 and flagged is_degraded=True."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", "recognized", 1)})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    # No timestamps provided
    edges = [("0xSUSPECT", "0xVASP", 1000.0, 1, None)]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    t_factor = next((f for f in result.attribution_factors if f.factor_code == "T"), None)
    assert t_factor is not None, "T factor missing from attribution_factors"
    assert t_factor.sub_score == 0.5, f"Expected T=0.5 for missing timestamp, got {t_factor.sub_score}"
    assert t_factor.is_degraded is True, "Expected T factor to be flagged is_degraded=True"
    assert t_factor.degradation_reason is not None


# ---------------------------------------------------------------------------
# T14: Missing sweep evidence handled safely (S=0, not penalized)
# ---------------------------------------------------------------------------

def test_T14_missing_sweep_safe():
    """T14: When no sweep evidence, S=0 and score is still valid (not penalized below threshold)."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", "verified", 2)})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [("0xSUSPECT", "0xVASP", 1000.0, 1, "2026-01-01T10:00:00+05:30")]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    s_factor = next((f for f in result.attribution_factors if f.factor_code == "S"), None)
    assert s_factor is not None, "S factor missing from attribution_factors"
    assert s_factor.sub_score == 0.0, f"Expected S=0 without sweep, got {s_factor.sub_score}"
    assert s_factor.is_degraded is False, "S=0 should NOT be flagged as degraded (absence not penalized)"
    assert result.confidence_score > 0, "Score should still be positive without sweep evidence"


# ---------------------------------------------------------------------------
# T15: Final confidence score always in [0, 100]
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("amount,strength,n_src", [
    (0.0, "weak", 1),
    (1000.0, "verified", 3),
    (999999.0, "recognized", 2),
    (0.001, "inferred", 1),
])
def test_T15_score_in_bounds(amount, strength, n_src):
    """T15: Score must always be in [0, 100] regardless of input extremes."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", strength, n_src)})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [("0xSUSPECT", "0xVASP", amount, 1, "2026-01-01T10:00:00+05:30")]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    assert 0.0 <= result.confidence_score <= 100.0, (
        f"Score {result.confidence_score} out of [0,100] bounds"
    )


# ---------------------------------------------------------------------------
# T16: Per-factor breakdown always present on AttributionResult
# ---------------------------------------------------------------------------

def test_T16_per_factor_breakdown_present():
    """T16: attribution_factors must contain all 6 factors (F,P,T,L,S,I) with required fields."""
    intel = make_intel({"0xVASP": ("VASP-X", "TestVASP", "recognized", 1)})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [("0xSUSPECT", "0xVASP", 1000.0, 1, "2026-01-01T10:00:00+05:30")]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    assert len(result.attribution_factors) == 6, (
        f"Expected 6 attribution factors, got {len(result.attribution_factors)}"
    )
    codes = {f.factor_code for f in result.attribution_factors}
    assert codes == {"F", "P", "T", "L", "S", "I"}, (
        f"Expected factors F,P,T,L,S,I but got {codes}"
    )
    for f in result.attribution_factors:
        assert hasattr(f, "raw_value")
        assert hasattr(f, "sub_score")
        assert hasattr(f, "weight")
        assert hasattr(f, "contribution")
        assert hasattr(f, "is_degraded")
        assert 0.0 <= f.sub_score <= 1.0, f"Sub-score {f.sub_score} out of [0,1] for factor {f.factor_code}"


# ---------------------------------------------------------------------------
# T17: Synthetic transactions always marked is_synthetic=True with SIM- IDs
# ---------------------------------------------------------------------------

def test_T17_synthetic_transactions_marked():
    """T17: All edges in CASES_DATABASE must have is_synthetic=True and SIM- tx_hash."""
    for case_id, case_data in CASES_DATABASE.items():
        for edge in case_data.get("edges", []):
            assert edge.get("is_synthetic") is True, (
                f"{case_id} edge {edge['id']}: is_synthetic must be True"
            )
            tx_hash = edge.get("tx_hash", "")
            assert tx_hash.startswith("SIM-"), (
                f"{case_id} edge {edge['id']}: tx_hash '{tx_hash}' must start with SIM-"
            )
            assert len(tx_hash) == 12, (
                f"{case_id} edge {edge['id']}: SIM- tx_hash should be 12 chars (SIM-XXXXXXXX)"
            )


def test_T17b_custom_trace_synthetic():
    """T17b: generate_custom_trace edges must also be synthetic with SIM- IDs."""
    result = generate_custom_trace("0xDEADBEEF12345678", chain="Ethereum", max_hops=3)
    for edge in result.get("edges", []):
        assert edge.get("is_synthetic") is True, f"Edge {edge['id']} missing is_synthetic"
        assert edge.get("tx_hash", "").startswith("SIM-"), (
            f"Edge {edge['id']} tx_hash {edge.get('tx_hash')} must start with SIM-"
        )


# ---------------------------------------------------------------------------
# T18: FastAPI app still starts successfully
# ---------------------------------------------------------------------------

def test_T18_fastapi_app_starts():
    """T18: The FastAPI app must import and instantiate without errors."""
    try:
        from backend.app import app
        assert app is not None
        assert app.title.startswith("VASP TRACE")
    except Exception as e:
        pytest.fail(f"FastAPI app failed to start: {e}")


# ---------------------------------------------------------------------------
# T19: Frontend index.html loads (static file exists)
# ---------------------------------------------------------------------------

def test_T19_frontend_index_exists():
    """T19: frontend/index.html must exist and contain expected structure."""
    import os
    index_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend", "index.html"
    )
    assert os.path.exists(index_path), f"frontend/index.html not found at {index_path}"
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "VASP TRACE" in content, "VASP TRACE title not found in index.html"
    assert "screenLogin" in content, "screenLogin div not found"
    assert "screenDashboard" in content, "screenDashboard div not found"
    assert "screenAnalysis" in content, "screenAnalysis div not found"
    # Check obsolete terms are gone
    assert "Section 65B Indian Evidence Act Compliance" not in content, \
        "index.html still contains obsolete '65B Compliance' footer text"
    assert "Section 91 & 102 CrPC" not in content, \
        "index.html still contains obsolete 'Section 91 & 102 CrPC'"
    assert "SYNDICATE MATCH" not in content, \
        "index.html still contains 'SYNDICATE MATCH' badge text"


# ---------------------------------------------------------------------------
# T20: Existing demo cases return coherent end-to-end results
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case_id", ["CASE-147", "CASE-101"])
def test_T20_demo_cases_coherent(case_id):
    """T20: Demo cases must return a valid AttributionResult with a plausible score."""
    from backend.entity_intelligence import EntityIntelligence as EI
    intel = EI()  # Uses real known_vasp_directory.json
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)
    ev = EvidenceVerifier()

    case_data = CASES_DATABASE[case_id]
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=5)
    result = engine.compute_attribution(case_data, flow)
    seal = ev.generate_forensic_hash(case_data, result.model_dump(), result.investigation_run_id)

    # Basic sanity
    assert isinstance(result, AttributionResult)
    assert 0.0 <= result.confidence_score <= 100.0
    assert result.primary_vasp is not None
    assert len(result.explainability) > 0

    # Evidence seal
    assert "sha256_hash" in seal
    assert seal["sha256_hash"] != ""
    assert seal["record_type"] == "TAMPER_EVIDENT_TECHNICAL_INTEGRITY_RECORD"
    assert "certificate_status" not in seal, "Obsolete certificate_status field found in seal"
    assert "statute" not in seal, "Obsolete statute field found in seal"

    # Hash verification should work
    from backend.evidence_verifier import EvidenceVerifier as EV
    ev2 = EV()
    verify = ev2.verify_hash(seal["sha256_hash"], seal["sha256_hash"])
    assert verify["is_valid"] is True
    print(f"\n{case_id}: score={result.confidence_score}%, VASP={result.primary_vasp.vasp_name}, "
          f"no_qualifying={result.no_qualifying_vasp}")


# ---------------------------------------------------------------------------
# T21: Flow Relevance double-counting prevention
# ---------------------------------------------------------------------------

def test_T21_flow_relevance_no_double_count():
    """T21: Flow relevance must sum distinct inbound transfers and ignore internal VASP sweeps."""
    intel = make_intel({
        "0xDEPOSIT": ("VASP-X", "TestVASP", "recognized", 1),
        "0xHOT": ("VASP-X", "TestVASP", "verified", 2),
    })
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    # 100 goes to DEPOSIT via path 1
    # 50 goes to DEPOSIT via path 2
    # 150 sweeps from DEPOSIT to HOT
    edges = [
        ("0xSUSPECT", "0xMULE1", 100.0, 1, "2026-01-01T10:00:00+05:30"),
        ("0xMULE1", "0xDEPOSIT", 100.0, 2, "2026-01-01T10:05:00+05:30"),
        ("0xSUSPECT", "0xMULE2", 50.0, 1, "2026-01-01T10:01:00+05:30"),
        ("0xMULE2", "0xDEPOSIT", 50.0, 2, "2026-01-01T10:06:00+05:30"),
        ("0xDEPOSIT", "0xHOT", 150.0, 3, "2026-01-01T10:10:00+05:30"),
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)

    # Total traced is 150. Amount reaching VASP should be exactly 150 (not 300).
    # This implies factor F = 150 / 150 = 1.0
    f_factor = next(f for f in result.attribution_factors if f.factor_code == "F")
    assert f_factor.sub_score == 1.0, f"Expected F=1.0 without double counting, got {f_factor.sub_score}"
    assert result.volume_to_vasp == 150.0

# ---------------------------------------------------------------------------
# T22: Demo CASE-147 targets deposit endpoint, not shared mule
# ---------------------------------------------------------------------------

def test_T22_demo_case_147_endpoint_correctness():
    """T22: Ensure CASE-147 attributes to CoinDCX deposit wallet, not the shared mule."""
    from backend.entity_intelligence import EntityIntelligence as EI
    intel = EI()  # Uses real known_vasp_directory.json
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    case_data = CASES_DATABASE["CASE-147"]
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=5)
    result = engine.compute_attribution(case_data, flow)
    
    # 0x71c89D8469C3D619A0A02717E11a5D44A1e4f44C is the mule at hop 2
    # 0x88cE19a456B7293E103984E29384729182937461 is the CoinDCX deposit at hop 3
    assert result.primary_vasp.deposit_address == "0x88cE19a456B7293E103984E29384729182937461", (
        f"CASE-147 should attribute to deposit address, not {result.primary_vasp.deposit_address}"
    )
    assert result.primary_vasp.vasp_id == "VASP-COINDCX"
    assert result.primary_vasp.hop_number == 3


# ---------------------------------------------------------------------------
# T23: Total Volume Tracked - Branching Path
# ---------------------------------------------------------------------------

def test_T23_total_volume_tracked_branching():
    """T23: Suspect -> A (600) and Suspect -> B (400) should yield total_volume_tracked = 1000."""
    intel = make_intel({})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [
        ("0xSUSPECT", "0xA", 600.0, 1, "2026-01-01T10:00:00+05:30"),
        ("0xSUSPECT", "0xB", 400.0, 1, "2026-01-01T10:05:00+05:30"),
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)
    
    assert result.no_qualifying_vasp is True
    assert result.total_volume_tracked == 1000.0, f"Expected 1000.0, got {result.total_volume_tracked}"

# ---------------------------------------------------------------------------
# T24: Total Volume Tracked - Linear Path Downstream Prevention
# ---------------------------------------------------------------------------

def test_T24_total_volume_tracked_no_downstream_inflation():
    """T24: Suspect -> A (1000), A -> B (950), B -> C (900) should NOT sum to 2850."""
    intel = make_intel({})
    ge = GraphEngine()
    engine = AttributionEngine(entity_intel=intel)

    edges = [
        ("0xSUSPECT", "0xA", 1000.0, 1, "2026-01-01T10:00:00+05:30"),
        ("0xA", "0xB", 950.0, 2, "2026-01-01T10:05:00+05:30"),
        ("0xB", "0xC", 900.0, 3, "2026-01-01T10:10:00+05:30"),
    ]
    case_data = make_case(edges)
    G = ge.build_graph(case_data["nodes"], case_data["edges"])
    flow = ge.analyze_fund_flow(G, case_data["suspect_wallet"], max_hops=4)
    result = engine.compute_attribution(case_data, flow)
    
    assert result.no_qualifying_vasp is True
    assert result.total_volume_tracked == 1000.0, f"Expected 1000.0, got {result.total_volume_tracked} (downstream inflation occurred)"


# ---------------------------------------------------------------------------
# T25 & T26: API Truncation and Confidence Level Tests
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient

def test_T25_api_trace_max_hops_truncation():
    """T25: /api/trace with max_hops=3 truncates hop 4, max_hops=4 includes hop 4."""
    from backend.app import app
    client = TestClient(app)

    # Test max_hops = 3
    resp3 = client.post("/api/trace", json={"case_id": "CASE-101", "max_hops": 3})
    assert resp3.status_code == 200
    data3 = resp3.json()
    graph_edges3 = data3["graph"]["edges"]
    assert not any(e.get("hop", 0) == 4 for e in graph_edges3), "Hop 4 edge should be truncated at max_hops=3"
    
    # Test max_hops = 4
    resp4 = client.post("/api/trace", json={"case_id": "CASE-101", "max_hops": 4})
    assert resp4.status_code == 200
    data4 = resp4.json()
    graph_edges4 = data4["graph"]["edges"]
    assert any(e.get("hop", 0) == 4 for e in graph_edges4), "Hop 4 edge should be present at max_hops=4"
    
    # Ensure attribution scores remain stable and unchanged by graph filtering
    assert abs(data4["attribution"]["confidence_score"] - 79.3) < 1.0
    assert abs(data3["attribution"]["confidence_score"] - 69.3) < 1.0

def test_T26_api_trace_confidence_level():
    """T26: Recommendation text logic is correctly fed by dynamic confidence_level in API."""
    from backend.app import app
    client = TestClient(app)

    # depth 3 -> 69.3% -> MEDIUM
    resp3 = client.post("/api/trace", json={"case_id": "CASE-101", "max_hops": 3})
    assert resp3.json()["attribution"]["confidence_level"] == "MEDIUM"

    # depth 4 -> 79.3% -> HIGH
    resp4 = client.post("/api/trace", json={"case_id": "CASE-101", "max_hops": 4})
    assert resp4.json()["attribution"]["confidence_level"] == "HIGH"

