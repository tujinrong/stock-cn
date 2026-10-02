import copy
import json
from urllib.parse import urlparse, parse_qs

import pytest

from stock_cn.universe import (
    bounded_prefilter, build_deep_research_pack,
    fetch_candidate_history, fetch_live_universe,
)


def clist_payload():
    rows = []
    # Enough supported rows to satisfy the minimum universe sanity check.
    for i in range(120):
        code = f"600{i:03d}"
        rows.append({
            "f12": code, "f13": 1, "f14": f"沪股{i}",
            "f2": 10 + i / 10, "f3": (i % 11) - 5,
            "f6": 1_000_000 + i * 10_000,
            "f8": 1 + i / 100,
            "f20": 10_000_000_000 + i * 100_000_000,
            "f21": 8_000_000_000 + i * 80_000_000,
        })
    rows += [
        {"f12": "000001", "f13": 0, "f14": "平安银行", "f2": 12, "f3": -2, "f6": 3e9, "f8": 1.2, "f20": 2e11, "f21": 1.8e11},
        {"f12": "002594", "f13": 0, "f14": "比亚迪", "f2": 100, "f3": -6, "f6": 8e9, "f8": 2.1, "f20": 8e11, "f21": 7e11},
        {"f12": "688001", "f13": 1, "f14": "科创样本", "f2": 20, "f3": -10, "f6": 9e9, "f8": 3, "f20": 1e11, "f21": 8e10},
        {"f12": "300750", "f13": 0, "f14": "创业板样本", "f2": 30, "f3": -9, "f6": 9e9, "f8": 3, "f20": 1e11, "f21": 8e10},
        {"f12": "920001", "f13": 0, "f14": "北交样本", "f2": 5, "f3": 1, "f6": 1e8, "f8": 1, "f20": 1e9, "f21": 9e8},
        {"f12": "600999", "f13": 1, "f14": "*ST测试", "f2": 3, "f3": -4, "f6": 2e8, "f8": 3, "f20": 2e9, "f21": 1e9},
    ]
    return {"data": {"total": len(rows), "diff": {str(i): x for i, x in enumerate(rows)}}}


def test_live_universe_excludes_unsupported_boards_and_tags_names():
    snap = fetch_live_universe(lambda url: clist_payload())
    symbols = {x["symbol"] for x in snap["rows"]}
    assert "000001.SZ" in symbols and "002594.SZ" in symbols
    assert "688001.SH" not in symbols
    assert "300750.SZ" not in symbols
    assert "920001.SZ" not in symbols
    st = next(x for x in snap["rows"] if x["symbol"] == "600999.SH")
    assert "ST_NAME" in st["risk_tags"]
    assert snap["eligible_count"] >= 100


def test_prefilter_is_bounded_and_explicitly_not_recommendation():
    snap = fetch_live_universe(lambda url: clist_payload())
    low = bounded_prefilter(snap, "LOW_RECOVERY", max_candidates=20)
    drop = bounded_prefilter(snap, "ABNORMAL_DROP", max_candidates=20)
    assert len(low["rows"]) <= 20
    assert len(drop["rows"]) <= 20
    assert low["not_a_recommendation"] is True
    assert "survivorship" in low["survivorship_warning"].lower()
    # BYD is a severe daily loser in this fixture and should make the abnormal-drop seed.
    assert "002594.SZ" in {x["symbol"] for x in drop["rows"]}


def fake_history_request(url):
    if "ifzq.gtimg.cn" not in url:
        raise RuntimeError("fallback should not be needed")
    q = parse_qs(urlparse(url).query)
    tx = q["param"][0].split(",")[0]
    rows = [
        ["2025-01-02", "10.00", "10.10", "10.20", "9.90", "100000"],
        ["2025-01-03", "10.15", "10.20", "10.30", "10.00", "120000"],
        ["2025-01-06", "10.25", "10.30", "10.40", "10.10", "130000"],
    ]
    return {"data": {tx: {"day": rows}}}


def test_candidate_history_builds_real_history_dataset_with_limits():
    snap = fetch_live_universe(lambda url: clist_payload())
    seed = bounded_prefilter(snap, "LOW_RECOVERY", max_candidates=10)
    seed["rows"] = seed["rows"][:2]
    data, attempts = fetch_candidate_history(
        seed, "2025-01-02", "2025-01-06", request=fake_history_request, max_symbols=10
    )
    assert data["kind"] == "REAL_HISTORY"
    assert len(data["instruments"]) == 2
    assert all(x["status"] == "OK" for x in attempts)
    # First day has no previous close in the requested window; later days do.
    symbol = next(iter(data["instruments"]))
    assert data["bars"]["2025-01-02"][symbol]["limit_up"] is None
    assert data["bars"]["2025-01-03"][symbol]["limit_up"] == "11.11"
    assert data["bars"]["2025-01-03"][symbol]["limit_down"] == "9.09"


def test_candidate_history_budget_is_hard_limit():
    snap = fetch_live_universe(lambda url: clist_payload())
    seed = bounded_prefilter(snap, "LOW_RECOVERY", max_candidates=20)
    with pytest.raises(ValueError, match="budget"):
        fetch_candidate_history(seed, "2025-01-02", "2025-01-06",
                                request=fake_history_request, max_symbols=10)


def test_unknown_prefilter_purpose_rejected():
    snap = fetch_live_universe(lambda url: clist_payload())
    with pytest.raises(ValueError, match="purpose"):
        bounded_prefilter(snap, "BUY_WINNERS", max_candidates=20)


def test_live_universe_falls_back_to_sina_without_mixing_partial_primary():
    def primary(url):
        raise RuntimeError("HTTP 502 simulated")

    pages = {}
    for node, market in (("sh_a", 1), ("sz_a", 0)):
        rows = []
        for i in range(60):
            code = (f"600{i:03d}" if market == 1 else f"000{i:03d}")
            rows.append({
                "symbol": ("sh" if market == 1 else "sz") + code,
                "code": code,
                "name": f"{node}{i}",
                "trade": str(10 + i / 10),
                "changepercent": str((i % 9) - 4),
                "amount": str(1000000 + i * 10000),
                "turnoverratio": "1.2",
            })
        pages[node] = rows

    def sina(url):
        q = parse_qs(urlparse(url).query)
        node = q["node"][0]
        page = int(q["page"][0])
        return pages[node] if page == 1 else []

    snap = fetch_live_universe(primary, fallback_request=sina)
    assert snap["source_provider"] == "Sina"
    assert snap["fallback_used"] is True
    assert "502" in snap["primary_failure"]
    assert snap["eligible_count"] == 120
    assert all(x["source_provider"] == "Sina" for x in snap["rows"])


def test_deep_research_pack_routes_attention_without_becoming_trade_signal():
    snap = fetch_live_universe(lambda url: clist_payload())
    seed = bounded_prefilter(snap, "LOW_RECOVERY", max_candidates=10)
    seed["rows"] = seed["rows"][:2]
    data, _ = fetch_candidate_history(
        seed, "2025-01-02", "2025-01-06", request=fake_history_request, max_symbols=10
    )
    pack = build_deep_research_pack(seed, data, data["sessions"][-1],
                                    "LOW_RECOVERY", max_candidates=2)
    assert pack["not_a_recommendation"] is True
    assert pack["selected_count"] <= 2
    assert all(x["not_a_trade_signal"] is True for x in pack["candidates"])
    assert all("research_state" in x for x in pack["candidates"])


def test_abnormal_drop_pack_does_not_call_fresh_drop_a_buy_signal():
    snap = fetch_live_universe(lambda url: clist_payload())
    seed = bounded_prefilter(snap, "ABNORMAL_DROP", max_candidates=10)
    # Force a supported severe loser into the small history sample.
    target = next(x for x in snap["rows"] if x["symbol"] == "002594.SZ")
    seed["rows"] = [target]
    seed["count"] = 1
    data, _ = fetch_candidate_history(
        seed, "2025-01-02", "2025-01-06", request=fake_history_request, max_symbols=10
    )
    pack = build_deep_research_pack(seed, data, data["sessions"][-1],
                                    "ABNORMAL_DROP", max_candidates=1)
    item = pack["candidates"][0]
    assert item["not_a_trade_signal"] is True
    assert "BUY" not in item["research_state"]


def test_ai_select_variant_prompt_receives_only_bounded_authorized_universe(repo):
    import copy
    from stock_cn.sim_data import fixture
    from stock_cn.sim_variants import VariantSimulation
    from stock_cn.variant_prompts import materialize
    from stock_cn.sim_agents import ScriptedSmokeAgent
    from stock_cn.simulation import ValidationError

    materialize(repo)
    data = fixture()
    keep = {"600036.SH", "600900.SH"}
    data["instruments"] = {s: m for s, m in data["instruments"].items() if s in keep}
    data["bars"] = {
        d: {s: b for s, b in rows.items() if s in keep}
        for d, rows in data["bars"].items()
    }
    data["candidate_research_pack"] = {
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": "LOW_RECOVERY",
        "not_a_recommendation": True,
        "candidates": [{"symbol": "600036.SH"}, {"symbol": "600900.SH"}],
    }
    data["universe_scope"] = {
        "authorized_symbols": sorted(keep),
        "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
        "not_full_a_share_claim": True,
    }
    sim = VariantSimulation(repo, "D", "D02", "bounded-ai-select", data)
    req = sim.prepare("2025-08-04")
    assert "AI_SELECT_DEEP_RESEARCH_PACK" in req["prompt"]
    assert "BOUNDED_RESEARCH_CANDIDATES_ONLY" in req["prompt"]
    assert "600036.SH" in req["prompt"] and "600900.SH" in req["prompt"]

    answer = ScriptedSmokeAgent().decide(req, [])
    answer["order_proposal"] = {
        "symbol": "600660.SH", "side": "BUY", "quantity": 100,
        "reference_price_cny": "50.00",
        "quote_time": req["context"]["information_cutoff"],
        "quote_source": "TEST_ONLY",
    }
    answer["action"] = "BUY"
    with pytest.raises(ValidationError, match="metadata"):
        sim.validate_decision(answer, req)
