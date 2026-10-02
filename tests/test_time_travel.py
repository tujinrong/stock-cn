import copy
from datetime import date, timedelta

from test_simulation import repo
from stock_cn.sim_data import fixture
from stock_cn.sim_variants import VariantSimulation
from stock_cn.time_travel import build_time_travel_context
from stock_cn.variant_prompts import materialize


def long_history():
    start = date(2025, 1, 2)
    sessions = [(start + timedelta(days=i)).isoformat() for i in range(300)]
    bars = {}
    instruments = {
        "600036.SH": {"name": "招商银行", "board": "MAIN", "lot_size": 100},
        "002594.SZ": {"name": "比亚迪", "board": "MAIN", "lot_size": 100},
    }
    for i, day in enumerate(sessions):
        bars[day] = {}
        for symbol, base in [("600036.SH", 40), ("002594.SZ", 90)]:
            open_p = base + i * 0.10
            close_p = base + i * 0.12
            bars[day][symbol] = {
                "open": f"{open_p:.2f}", "close": f"{close_p:.2f}",
                "high": f"{max(open_p, close_p)+0.30:.2f}",
                "low": f"{min(open_p, close_p)-0.30:.2f}",
                "volume": str(100000 + i * 100),
                "source": "TEST_ONLY:long-history",
            }
    return {
        "kind": "TEST_ONLY", "sessions": sessions, "bars": bars,
        "instruments": instruments, "evidence": [
            {"published_at": sessions[10] + "T10:00:00+08:00", "source": "TEST_NEWS",
             "text": "即使是过去新闻，默认时光穿越也可忽略"},
        ],
    }


def test_time_travel_builds_multi_timeframe_prefix_only():
    data = long_history()
    cutoff = data["sessions"][269]
    target = data["sessions"][270]
    ctx = build_time_travel_context(data, target, cutoff)
    assert ctx["target_date"] == target
    assert ctx["news_policy"] == "IGNORE_ARCHIVED_NEWS_BY_DEFAULT"
    assert ctx["market_proxy"]["kind"].endswith("NOT_BROAD_MARKET_INDEX")
    assert len(ctx["symbols"]) == 2
    for stock in ctx["symbols"]:
        assert stock["kline"]["daily_last20"]
        assert stock["kline"]["weekly_last12"]
        assert stock["kline"]["monthly_last12"]
        assert max(x["date"] for x in stock["kline"]["daily_last20"]) <= cutoff
        assert max(x["end"] for x in stock["kline"]["weekly_last12"]) <= cutoff
        assert max(x["end"] for x in stock["kline"]["monthly_last12"]) <= cutoff
        assert stock["moving_average"]["ma20"] is not None
        assert stock["returns_pct"]["60_sessions"] is not None
        assert stock["range_position_0_to_1"]["60_sessions"] is not None
        assert stock["range_position_0_to_1"]["250_sessions"] is not None
        assert stock["history_coverage"]["has_250_sessions"] is True
        assert stock["industry"]


def test_future_tail_changes_cannot_change_time_travel_context():
    one = long_history()
    two = copy.deepcopy(one)
    cutoff = one["sessions"][40]
    target = one["sessions"][41]
    for day in two["sessions"]:
        if day > cutoff:
            for bar in two["bars"][day].values():
                bar.update(open="999.00", close="1000.00", high="1001.00",
                           low="998.00", volume="99999999")
    two["evidence"].append({
        "published_at": two["sessions"][-1] + "T10:00:00+08:00",
        "source": "FUTURE", "text": "future winner",
    })
    assert build_time_travel_context(one, target, cutoff) == build_time_travel_context(two, target, cutoff)


def test_variant_prompt_uses_same_full_prompt_plus_travel_appendix(repo):
    materialize(repo)
    data = fixture()
    data["evidence"] = [{
        "published_at": "2025-08-01T10:00:00+08:00",
        "source": "TEST_NEWS", "text": "PAST_NEWS_DEFAULT_IGNORED",
    }]
    sim = VariantSimulation(repo, "A", "A02", "travel", data)
    req = sim.prepare("2025-08-04")
    assert "你现在回到2025-08-01收盘时" in req["prompt"]
    assert "2025-08-01T15:00:00+08:00" in req["prompt"]
    assert "下一交易日2025-08-04开盘模拟执行" in req["prompt"]
    assert "PAST_NEWS_DEFAULT_IGNORED" not in req["prompt"]
    travel = sim.store.path("requests/2025-08-04/time_travel.json")
    assert travel.exists()
    obj = __import__("json").loads(travel.read_text(encoding="utf-8"))
    assert obj["target_date"] == "2025-08-01"
    assert obj["knowledge_cutoff"] == "2025-08-01T15:00:00+08:00"
    assert obj["planned_execution_date"] == "2025-08-04"
    assert "IMMUTABLE_STRATEGY_START" in req["prompt"]
    assert "A02" in req["prompt"]


def test_variant_time_travel_prompt_is_idempotent(repo):
    materialize(repo)
    sim = VariantSimulation(repo, "A", "A02", "travel-repeat", fixture())
    one = sim.prepare("2025-08-04")
    two = sim.prepare("2025-08-04")
    assert one == two


def test_time_travel_jump_can_start_mid_history_without_fake_prior_trades(repo):
    materialize(repo)
    sim = VariantSimulation(repo, "A", "A02", "jump-mid", fixture())
    opening = sim.jump_initialize("2025-08-05")
    assert opening["date"] == "2025-08-05"
    assert opening["_meta"]["time_travel_jump"] is True
    assert len(sim.store.events()) == 1
    req = sim.prepare("2025-08-06")
    assert "你现在回到2025-08-05收盘时" in req["prompt"]
    manifest = __import__("json").loads((sim.store.root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["submode"] == "TIME_TRAVEL_JUMP"
    assert manifest["time_travel_target_date"] == "2025-08-05"
    assert manifest["planned_execution_date"] == "2025-08-06"
    assert "does not recreate trades before that date" in " ".join(manifest["limitations"])

def test_short_history_does_not_pretend_to_have_one_year_position():
    data = long_history()
    cutoff = data["sessions"][100]
    target = data["sessions"][101]
    ctx = build_time_travel_context(data, target, cutoff)
    for stock in ctx["symbols"]:
        assert stock["history_coverage"]["has_250_sessions"] is False
        assert stock["range_position_0_to_1"]["250_sessions"] is None

def test_structural_break_does_not_fake_abnormal_crash_signal():
    data = long_history()
    # Simulate a 3-for-1 style raw-price discontinuity near the target date.
    split_day = data["sessions"][260]
    for symbol in data["instruments"]:
        for day in data["sessions"][260:]:
            bar = data["bars"][day][symbol]
            for key in ("open", "close", "high", "low"):
                bar[key] = f"{float(bar[key]) / 3:.2f}"
    cutoff = data["sessions"][269]
    target = data["sessions"][270]
    ctx = build_time_travel_context(data, target, cutoff)
    for stock in ctx["symbols"]:
        br = stock["suspected_price_basis_break"]
        assert br is not None
        assert br["classification"] == "SUSPECTED_CORPORATE_ACTION_OR_DATA_BASIS_BREAK"
        assert stock["continuous_analysis_sessions"] == 10
        assert stock["returns_pct"]["20_sessions"] is None
        assert stock["moving_average"]["ma20"] is None
        assert stock["range_position_0_to_1"]["250_sessions"] is None
