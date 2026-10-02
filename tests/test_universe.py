import copy
import json
from urllib.parse import urlparse, parse_qs

import pytest

from stock_cn.universe import (
    bounded_prefilter, fetch_candidate_history, fetch_live_universe,
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
