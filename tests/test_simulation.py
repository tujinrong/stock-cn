"""No network or paid AI. All fixtures identify synthetic data explicitly."""
import copy
import json
import threading
from pathlib import Path

import pytest

from stock_cn.sim_data import fixture, fetch_daily, number, validate_dataset
from stock_cn.sim_agents import Budget, ScriptedSmokeAgent, decision_base, OpenAIResponsesAgent
from stock_cn.sim_cli import run_batch, formal_fingerprints
from stock_cn.simulation import Simulation, ValidationError, dumps, read_json, digest


@pytest.fixture
def repo(tmp_path):
    def put(path, content):
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if isinstance(content, str) else dumps(content), encoding="utf-8")
    data = fixture()
    put("AGENTS.md", "Only isolated simulation; no paid services or formal trading.\n")
    put("strategies/common.md", "AI, not a fixed signal formula.\n")
    rows = []
    for series in ("A", "C", "D", "E", "F"):
        variants = [series + f"{i:02d}" for i in range(1, 4)] if series != "F" else ["F01"]
        row = {"strategy_id": series, "type": "FIXED" if series in {"A", "C"} else "AI_SELECT",
               "variants": variants, "status": "DRAFT", "enabled": False}
        if row["type"] == "FIXED":
            row["symbols"] = list(data["instruments"])
        rows.append(row)
        put(f"strategies/{series}/prompt.md", "Discuss opportunity, downside and cash.\n")
        for v in variants:
            put(f"strategies/{series}/variants/{v}.md", f"# {v}\nEvidence-based investment intent.\n")
        put(f"strategies/{series}/ai_input_template.md", "\n".join("{{" + n + "}}" for n in (
            "RUN_CONTEXT", "HOLDINGS_JSON", "HOLDINGS_TABLE_ROWS", "PREVIOUS_DECISION_SUMMARY", "AUTHORIZED_UNIVERSE", "EVIDENCE_AND_TOOL_CONTEXT")))
        put(f"strategies/{series}/init.json", {"initial_capital_cny": 200000,
            "opening_method": "ASSUMED_EXISTING_PORTFOLIO" if series == "A" else "CASH_ONLY",
            "cash_weight": 0.25 if series == "A" else 1,
            "stocks": [{"symbol": s, "weight": 0.15} for s in data["instruments"]] if series == "A" else []})
        put(f"strategies/{series}/holdings.json", {"status": "NOT_INITIALIZED", "positions": [], "cash_cny": None})
    rows.append({"strategy_id": "B", "type": "RESERVED", "variants": []})
    put("strategies/index.json", {"strategies": rows})
    return tmp_path


def sim(repo, series="C", data=None, test_id="unit", variant=None):
    return Simulation(repo, series, variant or series + "01", test_id, data or fixture())


def decision(s, day="2025-08-04", action="BUY", quantity=100, symbol="600036.SH"):
    req = s.prepare(day)
    r = decision_base(req)
    r.update(action=action, summary="TEST_ONLY hand-written decision, not financial advice")
    if action != "HOLD":
        q = req["market"][symbol][-1]
        r["order_proposal"] = {"symbol": symbol, "side": action, "quantity": quantity,
                               "reference_price_cny": q["close"], "quote_time": req["context"]["information_cutoff"], "quote_source": q["source"]}
    return r


@pytest.mark.parametrize("series", ["A", "C", "D", "E", "F"])
def test_initialization_isolated_and_idempotent(repo, series):
    before = formal_fingerprints(repo)
    s = sim(repo, series)
    state = s.initialize()
    assert number(state["total_equity_cny"]) == 200000
    assert s.initialize() == state
    assert len(s.store.events()) == 1
    assert formal_fingerprints(repo) == before
    assert state["_meta"]["fees_cny"] == "0.00"
    if series == "A":
        assert len(state["positions"]) == 5
        assert number(state["cash_cny"]) >= 50000
        assert all(p["quantity"] % 100 == 0 and p["quantity"] == p["sellable_quantity"] for p in state["positions"])
    else:
        assert state["positions"] == [] and number(state["cash_cny"]) == 200000


def test_exact_cash_fees_and_t1(repo):
    s = sim(repo)
    d = decision(s)
    ex = s.apply("2025-08-04", d)
    assert ex["status"] == "FILLED"
    state = s.store.load()
    assert state["cash_cny"] == "195984.96"
    assert state["positions"][0]["sellable_quantity"] == 0
    assert state["total_equity_cny"] == "200004.96"
    ex2 = s.apply("2025-08-05", decision(s, "2025-08-05", "SELL"))
    assert ex2["status"] == "FILLED"
    assert s.store.load()["positions"] == []
    assert s.store.load()["cash_cny"] == "199997.91"


def test_duplicate_does_not_change_state(repo):
    s = sim(repo)
    d = decision(s)
    ex = s.apply("2025-08-04", d)
    old = s.store.load()
    assert s.apply("2025-08-04", d) == ex
    assert s.store.load() == old
    d["action"] = "SELL"
    with pytest.raises(ValidationError, match="conflicting"):
        s.apply("2025-08-04", d)


@pytest.mark.parametrize("quantity,expected", [(50,"BOARD_LOT"),(100000,"INSUFFICIENT_CASH_AT_EXECUTION_PRICE")])
def test_order_rejection_consumes_day(repo, quantity, expected):
    s = sim(repo)
    response = decision(s, quantity=quantity)
    result = s.apply("2025-08-04", response)
    assert result["reason"] == expected
    assert s.store.load()["cash_cny"] == "200000.00"
    assert s.prepare("2025-08-04")["completed"]


def test_hold_then_buy_same_day_forbidden(repo):
    s = sim(repo)
    hold = decision(s, action="HOLD")
    assert s.apply("2025-08-04", hold)["status"] == "NO_TRADE"
    changed = copy.deepcopy(hold)
    changed["action"] = "BUY"
    with pytest.raises(ValidationError):
        s.apply("2025-08-04", changed)


def test_oversell_rejected(repo):
    s = sim(repo)
    result = s.apply("2025-08-04", decision(s, action="SELL"))
    assert result["reason"] == "INSUFFICIENT_T1_SHARES"


@pytest.mark.parametrize("key,value", [("suspended",True),("limit_up","40.10")])
def test_unexecutable_market_rejected(repo, key, value):
    data = fixture()
    data["bars"]["2025-08-04"]["600036.SH"][key] = value
    s = sim(repo, data=data)
    assert s.apply("2025-08-04", decision(s))["status"] == "REJECTED"


def test_missing_daily_limits_no_assumed_fill(repo):
    data = fixture()
    del data["bars"]["2025-08-04"]["600036.SH"]["limit_up"]
    s = sim(repo, data=data)
    assert s.apply("2025-08-04", decision(s))["reason"] == "MISSING_DAILY_LIMIT_METADATA"


@pytest.mark.parametrize("value", [True,1.2,0,-100,"100",None])
def test_invalid_order_quantity(repo, value):
    s = sim(repo)
    with pytest.raises((ValueError, TypeError)):
        s.apply("2025-08-04", decision(s, quantity=value))
    assert len(s.store.events()) == 1


@pytest.mark.parametrize("field,value", [("mode","FORMAL"),("strategy_id","A"),("input_revision",999),
                                         ("input_revision",True),("date","2025-08-05"),("input_commit","wrong")])
def test_ai_identity_and_version_validation(repo, field, value):
    s = sim(repo)
    d = decision(s)
    d[field] = value
    with pytest.raises(ValidationError):
        s.apply("2025-08-04", d)
    assert len(s.store.events()) == 1


def test_future_price_rejected(repo):
    s = sim(repo)
    d = decision(s)
    d["order_proposal"]["quote_time"] = "2025-08-04T15:00:00+08:00"
    with pytest.raises(ValidationError, match="future"):
        s.apply("2025-08-04", d)


def test_future_evidence_rejected(repo):
    s = sim(repo)
    d = decision(s)
    d["evidence"] = [{"source":"fixture", "published_at":"2025-08-04T15:00:00+08:00"}]
    with pytest.raises(ValidationError, match="future"):
        s.apply("2025-08-04", d)


def test_current_day_and_future_news_not_in_prompt(repo):
    data = fixture()
    data["bars"]["2025-08-04"]["600036.SH"]["close"] = "9999.99"
    data["bars"]["2025-08-04"]["600036.SH"]["high"] = "10000.00"
    data["evidence"] = [{"published_at":"2025-08-04T12:00:00+08:00", "source":"fixture", "text":"FUTURE_SECRET"},
                        {"published_at":"2025-08-01T12:00:00+08:00", "source":"fixture", "text":"PAST_VISIBLE"}]
    request = sim(repo, data=data).prepare("2025-08-04")
    assert "9999.99" not in request["prompt"] and "FUTURE_SECRET" not in request["prompt"]
    assert "PAST_VISIBLE" in request["prompt"]
    assert "{{" not in request["prompt"]


@pytest.mark.parametrize("symbol", ["688001.SH","689009.SH","300001.SZ","000001.SH","600036.SZ"])
def test_wrong_or_excluded_board(repo, symbol):
    data = fixture()
    data["instruments"][symbol] = {"board":"MAIN","lot_size":100,"name":"TEST_ONLY"}
    with pytest.raises(ValueError):
        sim(repo, data=data)


def test_fixed_universe_cannot_expand(repo):
    data = fixture()
    data["instruments"]["600000.SH"] = {"board":"MAIN","lot_size":100,"name":"TEST_ONLY"}
    for bars in data["bars"].values():
        bars["600000.SH"] = copy.deepcopy(bars["600036.SH"])
    s = sim(repo, data=data)
    with pytest.raises(ValidationError, match="fixed universe"):
        s.apply("2025-08-04", decision(s, symbol="600000.SH"))


@pytest.mark.parametrize("test_id", ["../formal","a/b","", "..", "/tmp/output"])
def test_path_isolation(repo, test_id):
    with pytest.raises(ValidationError):
        sim(repo, test_id=test_id)


def test_no_reserved_series(repo):
    with pytest.raises(ValidationError):
        sim(repo, "B")


def test_symlink_escape(repo, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    p = repo / "strategies/C/simulations"
    p.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValidationError):
        sim(repo)


def test_ordered_sessions_and_changed_inputs(repo):
    s = sim(repo)
    with pytest.raises(ValidationError, match="in order"):
        s.prepare("2025-08-05")
    data = fixture()
    data["bars"]["2025-08-04"]["600036.SH"]["open"] = "40.11"
    with pytest.raises(ValidationError, match="new test_id"):
        sim(repo, data=data).initialize()


def test_missing_bar_halts_not_hold(repo):
    data = fixture()
    del data["bars"]["2025-08-04"]["600036.SH"]
    s = sim(repo, "A", data=data)
    with pytest.raises(ValidationError, match="missing"):
        s.prepare("2025-08-04")
    assert len(s.store.events()) == 1


def test_projection_repair_does_not_rewrite_events(repo):
    s = sim(repo)
    s.apply("2025-08-04", decision(s))
    event_bytes = [p.read_bytes() for p in s.store.path("events").glob("*.json")]
    s.store.write("holdings.json", {"cash_cny": -1})
    assert not s.store.audit()["ok"]
    assert s.store.audit(repair=True)["ok"]
    assert s.store.audit()["ok"]
    assert event_bytes == [p.read_bytes() for p in s.store.path("events").glob("*.json")]


def test_corrupt_event_must_not_be_auto_fixed(repo):
    s = sim(repo)
    s.initialize()
    p = s.store.path("events/000001.json")
    obj = read_json(p)
    obj["after"]["cash_cny"] = "9999999.00"
    p.write_text(dumps(obj))
    with pytest.raises(ValidationError, match="hash-chain"):
        s.store.audit(repair=True)


def test_crash_after_event_before_projection(repo, monkeypatch):
    s = sim(repo)
    d = decision(s)
    original = s.store.project
    monkeypatch.setattr(s.store, "project", lambda event: (_ for _ in ()).throw(OSError("injected crash")))
    with pytest.raises(OSError):
        s.apply("2025-08-04", d)
    monkeypatch.setattr(s.store, "project", original)
    assert s.store.audit(repair=True)["ok"]
    assert s.apply("2025-08-04", d)["status"] == "FILLED"
    assert len(s.store.events()) == 2


def test_exclusive_lock(repo):
    s = sim(repo)
    with s.store.lock():
        with pytest.raises(ValidationError, match="busy"):
            s.initialize()


def test_format_repair_is_bounded_and_visible(repo):
    s = sim(repo)
    budget = Budget(max_calls=2)
    agent = ScriptedSmokeAgent(budget, demonstrate_repair=True)
    assert s.run_day("2025-08-04", agent)["status"] == "FILLED"
    assert budget.calls == 2
    assert "校验反馈" in s.store.path("daily/2025-08-04/ai_input.md").read_text()
    assert len(s.store.events()) == 2


def test_budget_failure_never_creates_trade(repo):
    s = sim(repo)
    agent = ScriptedSmokeAgent(Budget(max_calls=1), demonstrate_repair=True)
    with pytest.raises(ValidationError, match="budget"):
        s.run_day("2025-08-04", agent)
    assert len(s.store.events()) == 1


def test_no_paid_api_by_default():
    with pytest.raises(ValidationError, match="allow-paid"):
        OpenAIResponsesAgent("any-model")


def test_parallel_isolation_full_run(repo):
    report = run_batch(repo, ["A01","A02","A03","C02","D02","E01","F01"], "parallel", fixture(), repair_demo=True)
    assert report["ok"] and report["formal_files_unchanged"]
    assert all(x["report"]["completed_days"] == 5 for x in report["results"])
    assert report["calls_used"] == 42


@pytest.mark.parametrize('layer', ['test_id', 'variant'])
def test_nested_simulation_link_cannot_alias_another_directory(repo, tmp_path_factory, layer):
    outside = tmp_path_factory.mktemp('nested-link-outside')
    base = repo / 'strategies/C/simulations'
    link = base / 'unit' if layer == 'test_id' else base / 'unit/C01'
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValidationError, match='symlink escape'):
        sim(repo)
    assert not list(outside.iterdir())


def test_multi_order_and_weight_validation(repo):
    s = sim(repo)
    d = decision(s)
    d["order_proposal"] = [d["order_proposal"]]
    with pytest.raises(ValidationError):
        s.apply("2025-08-04", d)
    d = decision(s)
    d.update(target_weights={"600036.SH":0.8}, target_cash_weight=0.5)
    with pytest.raises(ValidationError, match="sum"):
        s.apply("2025-08-04", d)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", None, True])
def test_nonfinite_amounts(value):
    with pytest.raises(ValueError):
        number(value)


def test_unadjusted_only_and_tick():
    data = fixture()
    data["price_basis"] = "qfq"
    with pytest.raises(ValueError, match="unadjusted"):
        validate_dataset(data)
    data = fixture()
    data["bars"][data["sessions"][0]]["600036.SH"]["open"] = "40.005"
    with pytest.raises(ValueError, match="tick"):
        validate_dataset(data)


def test_corporate_actions_fail_closed():
    data = fixture()
    data["corporate_actions"] = [{"symbol":"600036.SH", "dividend":1}]
    with pytest.raises(ValueError, match="corporate"):
        validate_dataset(data)


def test_source_fallback_and_raw_data_only():
    calls = []
    def request(url):
        calls.append(url)
        if "gtimg" in url:
            raise OSError("simulated primary outage")
        return {"data":{"klines":["2025-08-01,40,40.1,41,39,1000,40000", "2025-08-04,40.2,40.3,41,39,1000,40000"]}}
    data, attempts = fetch_daily(["600036.SH"], "2025-08-01", "2025-08-04", request)
    assert len(calls) == 2 and attempts[0]["provider"] == "Eastmoney"
    assert data["kind"] == "REAL_HISTORY" and data["fidelity"] == "FLOW_ONLY_REAL_PRICES"


def test_source_failure_not_fake_success():
    data, attempts = fetch_daily(["600036.SH"], "2025-08-01", "2025-08-04", lambda url: {})
    assert data is None and attempts[0]["status"] == "FAILED"


def test_partial_coverage_not_claim_full(repo):
    s = sim(repo)
    s.apply("2025-08-04", decision(s, action="HOLD"))
    report = s.report()
    assert not report["complete"] and report["completed_days"] == 1


def test_bad_json_is_repaired_with_feedback(repo):
    s = sim(repo)
    class Agent:
        calls = 0
        def decide(self, request, errors):
            self.calls += 1
            if self.calls == 1:
                return '{"broken":'
            result = decision_base(request)
            result["summary"] = "TEST_ONLY corrected JSON"
            return dumps(result)
    agent = Agent()
    assert s.run_day("2025-08-04", agent)["status"] == "NO_TRADE"
    assert agent.calls == 2


def test_format_failure_after_repair_limit(repo):
    s = sim(repo)
    class BadAgent:
        def decide(self, request, errors):
            return "not JSON"
    with pytest.raises(ValidationError, match="exhausted"):
        s.run_day("2025-08-04", BadAgent(), repairs=1)
    assert len(s.store.events()) == 1


def test_different_cash_opening_changes_fingerprint(repo):
    s = sim(repo)
    s.initialize()
    p = repo / "strategies/C/init.json"
    config = read_json(p)
    config["initial_capital_cny"] = 300000
    p.write_text(dumps(config))
    with pytest.raises(ValidationError, match="changed"):
        sim(repo).initialize()
