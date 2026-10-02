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


def official_pack(symbols=("600036.SH",), *, status="OK"):
    return {
        "kind": "OFFICIAL_DISCLOSURE_PACK",
        "provider": "CNINFO",
        "provider_official": True,
        "requested_start": "2026-06-01",
        "requested_end": "2026-10-08",
        "as_of": "2026-10-08T11:00:00+08:00",
        "symbols_requested": list(symbols),
        "symbols_ok_or_empty": list(symbols) if status in {"OK", "EMPTY"} else [],
        "symbols_failed": list(symbols) if status == "FAILED" else [],
        "complete_for_requested_symbols": status != "FAILED",
        "results": [
            {
                "symbol": s,
                "provider": "CNINFO",
                "provider_official": True,
                "provider_status": status,
                "items": [],
                **({"error": "TEST_PROVIDER_FAILURE"} if status == "FAILED" else {}),
            }
            for s in symbols
        ],
        "latest_periodic_report_refs": [],
        "important_recent_refs": [],
        "metadata_only": True,
        "financial_conclusions_extracted": False,
        "news_research_required": True,
    }


def financial_reviews(symbols):
    return {
        s: {
            "status": "REVIEWED",
            "as_of": "2026-10-08T10:50:00+08:00",
            "source_report": f"https://static.cninfo.com.cn/{s}.pdf",
            "source_official": True,
            "period": "2026H1",
            "facts": [{"name": "test-review", "value": True, "source": "official report"}],
            "summary": "TEST_ONLY reviewed latest disclosed financial information",
            "data_gaps": [],
        }
        for s in symbols
    }


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
        "official_disclosure_pack": official_pack(("600036.SH",)),
        "financial_reviews": financial_reviews(("600036.SH",)),
        "news_research": {"status": "SEARCHED", "items": []},
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
        "official_disclosure_pack": official_pack(("600036.SH", "600900.SH")),
        "financial_reviews": financial_reviews(("600036.SH", "600900.SH")),
        "news_research": {"status": "SEARCHED", "items": []},
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



def test_formal_buy_requires_successful_official_disclosure_coverage(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr("stock_cn.formal_paper._source_commit", lambda p: "TEST")
    session = FormalPaperSession(repo, "A", "A01")

    missing = live_snapshot()
    missing.pop("official_disclosure_pack")
    req = session.prepare(missing)
    with pytest.raises(ValueError, match="BUY research preflight failed"):
        session.validate_decision(response("FORMAL"), req)

    failed = live_snapshot()
    failed["official_disclosure_pack"] = official_pack(("600036.SH",), status="FAILED")
    req2 = session.prepare(failed)
    with pytest.raises(ValueError, match="BUY research preflight failed"):
        session.validate_decision(response("FORMAL"), req2)


def test_formal_sell_is_not_blocked_by_official_disclosure_provider_failure(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr("stock_cn.formal_paper._source_commit", lambda p: "TEST")
    session = FormalPaperSession(repo, "A", "A01")
    snap = live_snapshot()
    snap["official_disclosure_pack"] = official_pack(("600036.SH",), status="FAILED")
    req = session.prepare(snap)
    out = response("FORMAL")
    out["action"] = "SELL"
    out["order_proposal"]["side"] = "SELL"
    after, execution = session.execute_preview(out, req)
    assert execution["status"] == "FILLED"
    assert after["positions"][0]["quantity"] == 1900



def test_formal_buy_blocks_unreviewed_financials_or_unsearched_news(tmp_path, monkeypatch):
    repo = make_repo(tmp_path)
    monkeypatch.setattr("stock_cn.formal_paper._source_commit", lambda p: "TEST")

    no_fin = live_snapshot()
    no_fin["financial_reviews"] = {}
    session = FormalPaperSession(repo, "A", "A01")
    req = session.prepare(no_fin)
    with pytest.raises(ValueError, match="FINANCIAL_REVIEW_NOT_COMPLETED"):
        session.validate_decision(response("FORMAL"), req)

    no_news = live_snapshot()
    no_news["news_research"] = {"status": "NOT_CHECKED", "items": []}
    session2 = FormalPaperSession(repo, "A", "A01")
    req2 = session2.prepare(no_news)
    with pytest.raises(ValueError, match="RECENT_NEWS_NOT_VERIFIED"):
        session2.validate_decision(response("FORMAL"), req2)



def setup_formal_file_research(repo):
    root = repo / "research-inputs/D02/2026-10-08"
    write(root / "manifest.json", {
        "variant_id": "D02",
        "mode": "FORMAL",
        "decision_date": "2026-10-08",
        "information_cutoff": "2026-10-08T10:59:00+08:00",
        "source_commit": "TEST",
        "formal_execution": False,
    })
    reports = []
    financials = {}
    for symbol, name, value in (
        ("600036.SH", "招商银行", "TEST_BANK"),
        ("600900.SH", "长江电力", "TEST_POWER"),
    ):
        ref = {
            "symbol": symbol,
            "title": name + "2026年半年度报告",
            "published_at": "2026-08-30T00:00:00+08:00",
            "source_official": True,
            "source_provider": "TEST_OFFICIAL",
            "document_url": f"https://example.test/{symbol}.pdf",
            "is_periodic_report_body": True,
            "category": "PERIODIC_REPORT",
        }
        reports.append(ref)
        financials[symbol] = {
            "status": "REVIEWED",
            "symbol": symbol,
            "as_of": "2026-10-08T10:58:00+08:00",
            "source_report": ref["document_url"],
            "source_official": True,
            "period": "2026H1",
            "facts": [{
                "name": "净利润",
                "value": value,
                "source": "官方半年报",
            }],
            "summary": value,
            "data_gaps": [],
        }
    write(root / "official-disclosure-pack.json", {
        "kind": "OFFICIAL_DISCLOSURE_PACK",
        "symbols_requested": ["600036.SH", "600900.SH"],
        "results": [{
            "symbol": r["symbol"], "provider_status": "OK", "items": [r]
        } for r in reports],
        "latest_periodic_report_refs": reports,
        "important_recent_refs": [],
    })
    write(root / "financial-reviews.json", financials)
    write(root / "news-research.json", {
        "status": "NO_RELEVANT_RECENT_NEWS",
        "searched_at": "2026-10-08T10:58:30+08:00",
        "items": [],
    })
    write(root / "candidate-research-pack.json", {
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": "LOW_RECOVERY",
        "cutoff_date": "2026-10-08",
        "selected_count": 1,
        "not_a_recommendation": True,
        "candidates": [{"symbol": "600900.SH", "name": "长江电力"}],
    })
    write(root / "universe-scope.json", {
        "authorized_symbols": ["600900.SH"],
        "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
        "not_full_a_share_claim": True,
    })


def test_formal_preview_auto_loads_file_research_inputs(tmp_path, monkeypatch):
    repo = make_ai_repo(tmp_path)
    setup_formal_file_research(repo)
    monkeypatch.setattr("stock_cn.formal_paper._source_commit", lambda p: "TEST")
    snapshot = ai_live_snapshot()
    for key in (
        "official_disclosure_pack", "financial_reviews", "news_research",
        "candidate_research_pack", "universe_scope",
    ):
        snapshot.pop(key, None)

    session = FormalPaperSession(repo, "D", "D02")
    req = session.prepare(snapshot)
    assert req["live_snapshot"]["research_input_manifest"]["variant_id"] == "D02"
    assert req["decision_research_bundle"]["coverage"]["financial_interpretation_completed"] == 2
    assert "TEST_POWER" in req["prompt"]

    after, execution = session.execute_preview(
        ai_response(req, "BUY", "600900.SH"), req
    )
    assert execution["status"] == "FILLED"
    assert any(p["symbol"] == "600900.SH" for p in after["positions"])
