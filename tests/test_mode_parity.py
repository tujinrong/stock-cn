import copy
import json
from pathlib import Path

import pytest

from stock_cn.formal_paper import FormalPaperSession, cutover_readiness, validate_live_snapshot
from stock_cn.paper_core import execute_single_order
from stock_cn.variant_prompts import approve_simulation_prompt_for_formal, sha


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def account(mode="FORMAL"):
    return {
        "strategy_id": "A", "variant_id": "A01", "status": "ACTIVE",
        "date": "2026-10-08", "initial_capital_cny": "200000.00",
        "cash_cny": "100000.00", "total_equity_cny": "200000.00",
        "positions": [{
            "symbol": "600036.SH", "name": "招商银行", "quantity": 2000,
            "sellable_quantity": 2000, "average_cost_cny": "50.000000",
            "cost_basis_cny": "100000.00", "valuation_price_cny": "50.00",
        }],
        "_meta": {"mode": mode, "paper_only": True, "revision": 7,
                  "execution_enabled": True, "fees_cny": "0.00",
                  "valuation_time": "2026-10-08T10:55:00+08:00"},
    }


def response(mode="FORMAL"):
    return {
        "schema_version": "0.3-draft", "strategy_id": "A", "variant_id": "A01",
        "mode": mode, "run_id": "formal-A01-2026-10-08",
        "decision_id": "formal-A01-2026-10-08", "date": "2026-10-08",
        "decision_time": "2026-10-08T11:00:00+08:00", "input_revision": 7,
        "input_commit": "TEST", "status": "READY", "action": "BUY",
        "order_proposal": {
            "symbol": "600036.SH", "side": "BUY", "quantity": 100,
            "reference_price_cny": "50.00",
            "quote_time": "2026-10-08T10:59:30+08:00", "quote_source": "TEST_LIVE",
        },
        "target_weights": None, "target_cash_weight": None, "summary": "测试",
        "risks": [], "evidence": [], "data_gaps": [],
    }


def fees():
    return {"commission_rate": "0.00025", "min_commission": "5",
            "stamp_duty_sell_rate": "0.0005", "transfer_fee_rate": "0.00001"}


def test_shared_execution_core_has_mode_parity():
    state = account()
    quote = {"price": "50.00", "source": "TEST", "quote_time": "2026-10-08T10:59:30+08:00",
             "suspended": False, "limit_up": "55.00", "limit_down": "45.00"}
    instrument = {"name": "招商银行", "lot_size": 100}
    sim_resp = response("SIMULATION")
    formal_resp = response("FORMAL")
    sim_resp["decision_id"] = "sim"
    formal_resp["decision_id"] = "formal"
    sim_after, sim_ex = execute_single_order(
        state, sim_resp, quote, instrument, fees(), mode="SIMULATION",
        execution_basis="TEST_SAME_QUOTE", execution_time="2026-10-08T11:00:00+08:00")
    formal_after, formal_ex = execute_single_order(
        state, formal_resp, quote, instrument, fees(), mode="FORMAL",
        execution_basis="TEST_SAME_QUOTE", execution_time="2026-10-08T11:00:00+08:00")
    assert sim_after == formal_after
    assert sim_ex["fill"] == formal_ex["fill"]
    assert sim_ex["status"] == formal_ex["status"] == "FILLED"


def live_snapshot():
    return {
        "kind": "LIVE_SNAPSHOT", "market_date": "2026-10-08",
        "as_of": "2026-10-08T11:00:00+08:00", "fidelity": "LIVE_PAPER",
        "instruments": {"600036.SH": {"name": "招商银行", "board": "MAIN", "lot_size": 100}},
        "quotes": {"600036.SH": {
            "price": "50.00", "source": "TEST_LIVE",
            "quote_time": "2026-10-08T10:59:30+08:00",
            "limit_up": "55.00", "limit_down": "45.00", "suspended": False,
        }},
        "evidence": [{"source": "TEST", "published_at": "2026-10-08T10:30:00+08:00",
                      "title": "已知资料"}],
    }


def test_live_snapshot_rejects_stale_and_future_information():
    good = live_snapshot()
    assert validate_live_snapshot(good)
    stale = copy.deepcopy(good)
    stale["quotes"]["600036.SH"]["quote_time"] = "2026-10-08T10:40:00+08:00"
    with pytest.raises(ValueError, match="stale"):
        validate_live_snapshot(stale)
    future = copy.deepcopy(good)
    future["evidence"][0]["published_at"] = "2026-10-08T11:01:00+08:00"
    with pytest.raises(ValueError, match="future"):
        validate_live_snapshot(future)
    closed = copy.deepcopy(good)
    closed["as_of"] = "2026-10-08T12:00:00+08:00"
    closed["quotes"]["600036.SH"]["quote_time"] = "2026-10-08T11:30:00+08:00"
    with pytest.raises(ValueError, match="session"):
        validate_live_snapshot(closed)


def make_repo(tmp_path):
    prompt = """# A01 full
{{RUN_CONTEXT}}
{{HOLDINGS_JSON}}
{{HOLDINGS_TABLE_ROWS}}
{{PREVIOUS_DECISION_SUMMARY}}
{{AUTHORIZED_UNIVERSE}}
{{EVIDENCE_AND_TOOL_CONTEXT}}
BUY SELL HOLD INSUFFICIENT_DATA
"""
    write(tmp_path / "strategies/A/variants/A01/prompt.md", prompt)
    write(tmp_path / "strategies/A/variants/A01/prompt_versions/v000.md", prompt)
    write(tmp_path / "strategies/A/variants/A01/simulation_prompt.json",
          {"version": "v000", "path": "prompt.md", "sha256": sha(prompt), "scope": "NEW_SIMULATION_ONLY"})
    write(tmp_path / "strategies/A/variants/A01/formal_prompt.json",
          {"version": "v000", "path": "prompt.md", "sha256": sha(prompt),
           "scope": "FORMAL_BASELINE_NOT_EXECUTION_AUTHORIZATION"})
    write(tmp_path / "strategies/A/variants/A01/holdings.json", account())
    write(tmp_path / "strategies/index.json", {
        "formal_execution_enabled": False, "evaluation_start": "2026-10-08",
        "evaluation_end": "2026-12-08",
        "strategies": [{"strategy_id": "A", "type": "FIXED", "symbols": ["600036.SH"],
                        "variants": ["A01"]}],
        "variants": [{"variant_id": "A01", "series_id": "A", "status": "DRAFT", "enabled": False}],
    })
    write(tmp_path / "config/default.json", fees())
    return tmp_path


def test_cutover_is_separate_from_prompt_promotion_and_execution(tmp_path):
    repo = make_repo(tmp_path)
    report = cutover_readiness(repo, "A01")
    assert report["checks"]["same_prompt_hash"]
    assert not report["ready"]
    newer = (repo / "strategies/A/variants/A01/prompt.md").read_text() + "\n# clarity only\n"
    write(repo / "strategies/A/variants/A01/prompt_versions/v001.md", newer)
    write(repo / "strategies/A/variants/A01/simulation_prompt.json",
          {"version": "v001", "path": "prompt_versions/v001.md", "sha256": sha(newer),
           "scope": "NEW_SIMULATION_ONLY"})
    report = cutover_readiness(repo, "A01")
    assert not report["checks"]["same_prompt_hash"]
    with pytest.raises(ValueError, match="authorization"):
        approve_simulation_prompt_for_formal(repo, "A01", expected_version="v001", authorized=False)


def test_formal_prepare_and_preview_use_same_decision_contract(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr("stock_cn.formal_paper._source_commit", lambda p: "TEST")
    session = FormalPaperSession(repo, "A", "A01")
    req = session.prepare(live_snapshot())
    assert req["context"]["mode"] == "FORMAL"
    assert "{{" not in req["prompt"]
    out = response("FORMAL")
    after, execution = session.execute_preview(out, req)
    assert execution["status"] == "FILLED"
    assert after["positions"][0]["quantity"] == 2100
    assert after["cash_cny"] == "94994.95"
    # Preview is deliberately non-persistent.
    assert read_json(repo / "strategies/A/variants/A01/holdings.json")["positions"][0]["quantity"] == 2000


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
