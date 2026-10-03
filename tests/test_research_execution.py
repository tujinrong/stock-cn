import copy
import json

import pytest

from test_simulation import repo
from test_research_decision import (
    buy_decision,
    one_symbol_data,
    setup_research,
)
from stock_cn.research_decision import (
    lock_research_only_decision,
    prepare_research_only_request,
)
from stock_cn.research_execution import settle_locked_research_decision
from stock_cn.variant_prompts import materialize
from stock_cn.simulation import ValidationError


def prepare_locked(repo, test_id, target="2025-08-07"):
    materialize(repo)
    setup_research(repo, date=target, include_financial=True)
    data = one_symbol_data(target="2025-08-08")
    req = prepare_research_only_request(repo, "D02", test_id, data, target)
    decision = buy_decision(req)
    lock_research_only_decision(repo, "D02", test_id, target, decision)
    return data, req, decision


def truncate(data, through):
    out = copy.deepcopy(data)
    out["sessions"] = [d for d in out["sessions"] if d <= through]
    out["bars"] = {d: rows for d, rows in out["bars"].items() if d <= through}
    return out


def test_locked_research_decision_waits_without_next_session(repo):
    data, _, _ = prepare_locked(repo, "deferred-wait")
    target = "2025-08-07"
    waiting = settle_locked_research_decision(
        repo, "deferred-wait", "D02", target,
        truncate(data, target),
        check_through=target,
    )
    assert waiting["status"] == "WAITING_FOR_REAL_NEXT_SESSION_DATA"
    root = repo / "runs/research-decisions/deferred-wait/D02/2025-08-07"
    assert not (root / "execution.json").exists()
    assert not (root / "settlement.json").exists()


def test_locked_research_decision_uses_first_real_next_open_once(repo):
    data, _, _ = prepare_locked(repo, "deferred-fill")
    result = settle_locked_research_decision(
        repo, "deferred-fill", "D02", "2025-08-07",
        data, check_through="2025-08-08",
    )
    assert result["status"] == "SETTLED"
    assert result["execution_date"] == "2025-08-08"
    assert result["execution"]["status"] == "FILLED"
    assert result["execution"]["fill"]["price_cny"] == "40.50"
    pos = result["holdings_after"]["positions"][0]
    assert pos["symbol"] == "600036.SH"
    assert pos["quantity"] == 100
    assert result["future_execution_data_seen_by_decision"] is False
    assert result["formal_state_changed"] is False

    again = settle_locked_research_decision(
        repo, "deferred-fill", "D02", "2025-08-07",
        data, check_through="2025-08-08",
    )
    assert again == result


def test_waiting_attempt_can_later_settle(repo):
    data, _, _ = prepare_locked(repo, "deferred-later")
    target = "2025-08-07"
    first = settle_locked_research_decision(
        repo, "deferred-later", "D02", target,
        truncate(data, target), check_through=target,
    )
    assert first["status"].startswith("WAITING")
    second = settle_locked_research_decision(
        repo, "deferred-later", "D02", target,
        data, check_through="2025-08-08",
    )
    assert second["status"] == "SETTLED"
    assert second["execution_date"] == "2025-08-08"


def test_tampered_locked_decision_cannot_be_settled(repo):
    data, _, _ = prepare_locked(repo, "deferred-tamper")
    p = repo / "runs/research-decisions/deferred-tamper/D02/2025-08-07/decision.json"
    obj = json.loads(p.read_text())
    obj["summary"] = "tampered after lock"
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValidationError, match="changed after lock"):
        settle_locked_research_decision(
            repo, "deferred-tamper", "D02", "2025-08-07",
            data, check_through="2025-08-08",
        )
