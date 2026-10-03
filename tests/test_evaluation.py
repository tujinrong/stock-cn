import copy
import json
import shutil
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from test_simulation import repo
from stock_cn.evaluation import (
    prepare_batch, save_locked_decision, score_locked_decision, summarize,
)
from stock_cn.sim_agents import decision_base
from stock_cn.sim_data import SYMBOLS, validate_dataset
from stock_cn.simulation import read_json, ValidationError
from stock_cn.variant_prompts import materialize


def history(days=70, break_after=None):
    start = date(2025, 1, 2)
    sessions = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    bases = {
        "600036.SH": Decimal("40"), "002594.SZ": Decimal("90"),
        "600660.SH": Decimal("50"), "600900.SH": Decimal("28"),
        "601100.SH": Decimal("100"),
    }
    bars = {}
    for i, day in enumerate(sessions):
        bars[day] = {}
        for s, base in bases.items():
            trend = Decimal(i) * (Decimal("0.20") if s == "600036.SH" else Decimal("0.03"))
            close = base + trend
            if break_after is not None and i >= break_after and s == "600036.SH":
                close = close / Decimal("3")
            open_ = close - Decimal("0.05")
            bars[day][s] = {
                "open": f"{open_:.2f}", "close": f"{close:.2f}",
                "high": f"{close + Decimal('0.20'):.2f}",
                "low": f"{open_ - Decimal('0.20'):.2f}",
                "volume": str(100000 + i * 1000),
                "source": "TEST_ONLY:evaluation-history", "suspended": False,
                "limit_up": f"{close * Decimal('1.10'):.2f}",
                "limit_down": f"{close * Decimal('0.90'):.2f}",
            }
    data = {
        "schema_version": "0.4", "kind": "TEST_ONLY", "price_basis": "unadjusted",
        "fidelity": "ENGINEERING_ONLY", "sessions": sessions,
        "calendar_source": "test", "bars": bars,
        "instruments": {s: {"name": n, "board": "MAIN", "lot_size": 100}
                        for s, n in SYMBOLS.items()},
        "evidence": [], "corporate_actions": [],
        "limitations": ["TEST_ONLY evaluation fixture"],
    }
    validate_dataset(data)
    return data


def make_buy_decision(repo, eval_id, variant, target_date):
    entry = read_json(repo / "runs/evaluations" / eval_id / "entries" / variant / f"{target_date}.json")
    request = read_json(repo / entry["request_path"])
    d = decision_base(request)
    row = request["market"]["600036.SH"][-1]
    d.update(
        action="BUY",
        summary="TEST_ONLY：只根据历史截止时点可见价格决定买入100股，用于评价管线验证。",
        risks=["历史资料有限。"],
        data_gaps=["没有历史新闻和完整财务。"],
        order_proposal={
            "symbol": "600036.SH", "side": "BUY", "quantity": 100,
            "reference_price_cny": row["close"],
            "quote_time": request["context"]["information_cutoff"],
            "quote_source": row["source"],
        },
    )
    return d, request


def test_prepare_has_no_future_outcome_and_does_not_touch_formal(repo):
    materialize(repo)
    data = history()
    target = data["sessions"][8]
    before = read_json(repo / "strategies/C/variants/C02/holdings.json")
    m = prepare_batch(repo, "ev1", ["C02"], data, [target])
    assert m["future_outcomes_in_prompt"] is False
    e = m["entries"][0]
    assert '\\' not in e['request_path']
    prompt = (repo / e["ai_input_path"]).read_text(encoding="utf-8")
    assert data["sessions"][-1] not in prompt
    assert "future_outcomes" not in prompt.lower()
    assert not (repo / "runs/evaluations/ev1/scores").exists()
    assert read_json(repo / "strategies/C/variants/C02/holdings.json") == before


def test_unavailable_decision_has_no_fake_hold_performance(repo):
    materialize(repo)
    data = history()
    target = data['sessions'][8]
    entry = prepare_batch(repo, 'missing-data', ['E03'], data, [target])['entries'][0]
    request = read_json(repo / entry['request_path'])
    answer = decision_base(request)
    answer.update(status='INSUFFICIENT_DATA', action=None, summary='Missing historical industry evidence')
    save_locked_decision(repo, 'missing-data', 'E03', target, answer)
    result = score_locked_decision(repo, 'missing-data', 'E03', target, data)
    assert result['execution']['status'] == 'NOT_EXECUTED'
    assert all(s['status'] == 'DECISION_UNAVAILABLE' and 'actual_return_pct' not in s for s in result['scores'])
    assert len(list((repo / Path(entry['request_path']).parent.parent.parent / 'events').glob('*.json'))) == 1


def test_prompt_content_tamper_is_rejected_even_if_hash_field_unchanged(repo):
    materialize(repo)
    data = history()
    target = data['sessions'][8]
    entry = prepare_batch(repo, 'prompt-tamper', ['C02'], data, [target])['entries'][0]
    decision, request = make_buy_decision(repo, 'prompt-tamper', 'C02', target)
    save_locked_decision(repo, 'prompt-tamper', 'C02', target, decision)
    request['prompt'] += '\nFUTURE_WINNER_SECRET'
    (repo / entry['request_path']).write_text(json.dumps(request), encoding='utf-8')
    with pytest.raises(ValidationError, match='prompt content changed'):
        score_locked_decision(repo, 'prompt-tamper', 'C02', target, data)


def test_same_historical_prefix_same_prompt_even_if_future_changes(repo, tmp_path_factory):
    materialize(repo)
    other = tmp_path_factory.mktemp("eval-prefix")
    shutil.copytree(repo, other, dirs_exist_ok=True)
    one = history()
    two = copy.deepcopy(one)
    target = one["sessions"][8]
    for d in two["sessions"][20:]:
        two["bars"][d]["600036.SH"].update(
            open="900.00", close="901.00", high="902.00", low="899.00")
    a = prepare_batch(repo, "same", ["C02"], one, [target])["entries"][0]
    b = prepare_batch(other, "same", ["C02"], two, [target])["entries"][0]
    assert (repo / a["ai_input_path"]).read_text() == (other / b["ai_input_path"]).read_text()
    assert a["prompt_sha256"] == b["prompt_sha256"]


def test_decision_lock_is_immutable_and_score_is_post_lock_only(repo):
    materialize(repo)
    data = history()
    target = data["sessions"][8]
    prepare_batch(repo, "ev2", ["C02"], data, [target])
    decision, request = make_buy_decision(repo, "ev2", "C02", target)
    lock = save_locked_decision(repo, "ev2", "C02", target, decision)
    assert lock["future_outcomes_seen_by_decision_phase"] is False
    with pytest.raises(ValidationError, match="already locked"):
        save_locked_decision(repo, "ev2", "C02", target, decision)
    result = score_locked_decision(repo, "ev2", "C02", target, data, (5, 20, 40))
    assert result["future_outcomes_were_separate_from_decision_phase"] is True
    assert result["eligible_for_prompt_auto_improvement"] is False
    assert result["execution"]["status"] == "FILLED"
    assert all(x["status"] == "SCORED" for x in result["scores"])
    assert [x['elapsed_sessions'] for x in result['scores']] == [6, 21, 41]
    assert all(x['max_daily_drawdown_pct'] >= 0 for x in result['scores'])
    from stock_cn.performance import annualized_pct
    assert result['scores'][-1]['annualized_return_pct'] == pytest.approx(
        annualized_pct(result['scores'][-1]['actual_return_pct'], 41))
    assert Decimal(result["scores"][0]["incremental_pnl_vs_hold_cny"]) > 0
    assert request["prompt_sha256"] == result["prompt_sha256"]
    s = summarize(repo, "ev2")
    assert s["scored_entries"] == 1
    assert s["variant_aggregates"][0]["scored_40d_count"] == 1
    assert s["variant_aggregates"][0]["annualized_from_average_40d_pct"] is not None
    assert s["annualization"]["reference_sessions"] == 40
    text = (repo / "runs/evaluations/ev2/summary.md").read_text(encoding="utf-8")
    assert "折算年化" in text
    comparison = read_json(repo / 'runs/evaluations/ev2/comparison.json')
    assert len(comparison) == 3
    assert comparison[-1]['completed_days'] == 41
    assert comparison[-1]['future_data_check'] == 'PASS_LOCK_AND_PREFIX'


def test_future_structural_break_is_invisible_to_prompt_but_blocks_score(repo):
    materialize(repo)
    data = history(break_after=20)
    target = data["sessions"][8]
    prepare_batch(repo, "ev3", ["C02"], data, [target])
    decision, _ = make_buy_decision(repo, "ev3", "C02", target)
    save_locked_decision(repo, "ev3", "C02", target, decision)
    result = score_locked_decision(repo, "ev3", "C02", target, data, (5, 20, 40))
    m = {x["horizon_sessions"]: x for x in result["scores"]}
    assert m[5]["status"] == "SCORED"
    assert m[20]["status"] == "UNSCORABLE_PRICE_BASIS_BREAK"
    entry = read_json(repo / "runs/evaluations/ev3/entries/C02" / f"{target}.json")
    prompt = (repo / entry["ai_input_path"]).read_text()
    assert data["sessions"][20] not in prompt


def test_changed_locked_decision_is_rejected(repo):
    materialize(repo)
    data = history()
    target = data["sessions"][8]
    prepare_batch(repo, "ev4", ["C02"], data, [target])
    decision, _ = make_buy_decision(repo, "ev4", "C02", target)
    save_locked_decision(repo, "ev4", "C02", target, decision)
    p = repo / "runs/evaluations/ev4/decisions/C02" / f"{target}.json"
    obj = json.loads(p.read_text())
    obj["summary"] = "tampered"
    p.write_text(json.dumps(obj, ensure_ascii=False))
    with pytest.raises(ValidationError, match="changed"):
        score_locked_decision(repo, "ev4", "C02", target, data, (5,))

def test_retrieval_timestamp_does_not_change_semantic_evaluation_identity(repo):
    materialize(repo)
    data = history()
    data["retrieved_at"] = "2025-10-01T00:00:00+00:00"
    target = data["sessions"][8]
    prepare_batch(repo, "ev-retrieved", ["C02"], data, [target])
    decision, _ = make_buy_decision(repo, "ev-retrieved", "C02", target)
    save_locked_decision(repo, "ev-retrieved", "C02", target, decision)
    refetched = copy.deepcopy(data)
    refetched["retrieved_at"] = "2025-10-02T00:00:00+00:00"
    result = score_locked_decision(repo, "ev-retrieved", "C02", target, refetched, (5,))
    assert result["scores"][0]["status"] == "SCORED"
