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



def ai_account():
    return {
        "strategy_id": "D", "variant_id": "D02", "status": "ACTIVE",
        "date": "2026-10-08", "initial_capital_cny": "200000.00",
        "cash_cny": "150000.00", "total_equity_cny": "200000.00",
        "positions": [{
            "symbol": "600036.SH", "name": "招商银行", "quantity": 1000,
            "sellable_quantity": 1000, "average_cost_cny": "50.000000",
            "cost_basis_cny": "50000.00", "valuation_price_cny": "50.00",
        }],
        "_meta": {"mode": "FORMAL", "paper_only": True, "revision": 3,
                  "execution_enabled": True, "fees_cny": "0.00",
                  "valuation_time": "2026-10-08T10:55:00+08:00"},
    }


def ai_live_snapshot():
    return {
        "kind": "LIVE_SNAPSHOT", "market_date": "2026-10-08",
        "as_of": "2026-10-08T11:00:00+08:00", "fidelity": "LIVE_PAPER",
        "instruments": {
            "600036.SH": {"name": "招商银行", "board": "MAIN", "lot_size": 100},
            "600900.SH": {"name": "长江电力", "board": "MAIN", "lot_size": 100},
        },
        "quotes": {
            "600036.SH": {
                "price": "50.00", "source": "TEST_LIVE",
                "quote_time": "2026-10-08T10:59:30+08:00",
                "limit_up": "55.00", "limit_down": "45.00", "suspended": False,
            },
            "600900.SH": {
                "price": "30.00", "source": "TEST_LIVE",
                "quote_time": "2026-10-08T10:59:30+08:00",
                "limit_up": "33.00", "limit_down": "27.00", "suspended": False,
            },
        },
        "evidence": [],
        "candidate_research_pack": {
            "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
            "purpose": "LOW_RECOVERY",
            "cutoff_date": "2026-10-08",
            "selected_count": 1,
            "not_a_recommendation": True,
            "candidates": [{"symbol": "600900.SH", "name": "长江电力"}],
        },
        "universe_scope": {
            "authorized_symbols": ["600900.SH"],
            "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
            "not_full_a_share_claim": True,
        },
    }


def make_ai_repo(tmp_path):
    prompt = """# D02 full
{{RUN_CONTEXT}}
{{HOLDINGS_JSON}}
{{HOLDINGS_TABLE_ROWS}}
{{PREVIOUS_DECISION_SUMMARY}}
{{AUTHORIZED_UNIVERSE}}
{{EVIDENCE_AND_TOOL_CONTEXT}}
BUY SELL HOLD INSUFFICIENT_DATA
"""
    root = tmp_path / "strategies/D/variants/D02"
    write(root / "prompt.md", prompt)
    write(root / "prompt_versions/v000.md", prompt)
    write(root / "simulation_prompt.json",
          {"version": "v000", "path": "prompt.md", "sha256": sha(prompt), "scope": "NEW_SIMULATION_ONLY"})
    write(root / "formal_prompt.json",
          {"version": "v000", "path": "prompt.md", "sha256": sha(prompt),
           "scope": "FORMAL_PROMPT_APPROVED_NOT_EXECUTION_AUTHORIZATION"})
    write(root / "holdings.json", ai_account())
    write(root / "research_state.json", {
        "variant_id": "D02", "series_id": "D", "mode": "FORMAL",
        "status": "RESEARCH_READY", "date": "2026-10-08", "revision": 1,
        "candidate_watchlist": [], "last_candidate_pack": None,
        "last_broad_universe_source": {"provider": "TEST"},
        "universe_scope": {"authorized_symbols": ["600900.SH"]},
        "last_research_payload_sha256": "TEST",
        "last_decision_summary": None, "formal_research_enabled": True,
    })
    write(tmp_path / "strategies/index.json", {
        "formal_execution_enabled": True,
        "evaluation_start": "2026-10-08", "evaluation_end": "2026-12-08",
        "strategies": [{
            "strategy_id": "D", "type": "AI_SELECT", "variants": ["D02"],
        }],
        "variants": [{
            "variant_id": "D02", "series_id": "D", "status": "READY", "enabled": True,
        }],
    })
    write(tmp_path / "config/default.json", fees())
    return tmp_path


def ai_response(req, side, symbol, quantity=100):
    price = req["live_snapshot"]["quotes"][symbol]["price"]
    quote_time = req["live_snapshot"]["quotes"][symbol]["quote_time"]
    source = req["live_snapshot"]["quotes"][symbol]["source"]
    c = req["context"]
    return {
        "schema_version": "0.3-draft",
        "strategy_id": "D", "variant_id": "D02", "mode": "FORMAL",
        "run_id": c["run_id"], "decision_id": c["decision_id"],
        "date": c["date"], "decision_time": c["decision_time"],
        "input_revision": c["input_revision"], "input_commit": c["input_commit"],
        "status": "READY", "action": side,
        "order_proposal": {
            "symbol": symbol, "side": side, "quantity": quantity,
            "reference_price_cny": price, "quote_time": quote_time,
            "quote_source": source,
        },
        "target_weights": None, "target_cash_weight": None,
        "summary": "AI_SELECT contract test", "risks": [], "evidence": [], "data_gaps": [],
    }


def test_ai_select_formal_requires_candidate_pack(tmp_path, monkeypatch):
    repo = make_ai_repo(tmp_path)
    monkeypatch.setattr("stock_cn.formal_paper._source_commit", lambda p: "TEST")
    session = FormalPaperSession(repo, "D", "D02")
    bad = ai_live_snapshot()
    bad.pop("candidate_research_pack")
    with pytest.raises(ValueError, match="candidate research pack"):
        session.prepare(bad)


def test_ai_select_buy_must_be_candidate_but_existing_holding_can_be_sold(tmp_path, monkeypatch):
    repo = make_ai_repo(tmp_path)
    monkeypatch.setattr("stock_cn.formal_paper._source_commit", lambda p: "TEST")
    session = FormalPaperSession(repo, "D", "D02")
    req = session.prepare(ai_live_snapshot())

    # Existing 600036 position is intentionally not in today's buy candidate pool.
    with pytest.raises(ValueError, match="outside today's bounded candidate pool"):
        session.validate_decision(ai_response(req, "BUY", "600036.SH"), req)

    after_sell, sold = session.execute_preview(ai_response(req, "SELL", "600036.SH"), req)
    assert sold["status"] == "FILLED"
    assert after_sell["positions"][0]["quantity"] == 900

    after_buy, bought = session.execute_preview(ai_response(req, "BUY", "600900.SH"), req)
    assert bought["status"] == "FILLED"
    assert any(p["symbol"] == "600900.SH" and p["quantity"] == 100
               for p in after_buy["positions"])


def test_ai_select_cutover_requires_research_enablement(tmp_path):
    repo = make_ai_repo(tmp_path)
    ready = cutover_readiness(repo, "D02")
    assert ready["checks"]["formal_research_enabled"] is True
    assert ready["ready"] is True

    state_path = repo / "strategies/D/variants/D02/research_state.json"
    state = read_json(state_path)
    state["formal_research_enabled"] = False
    write(state_path, state)
    blocked = cutover_readiness(repo, "D02")
    assert blocked["checks"]["formal_research_enabled"] is False
    assert blocked["ready"] is False
