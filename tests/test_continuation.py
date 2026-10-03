import copy

from test_simulation import repo
from test_research_execution import prepare_locked
from stock_cn.continuation import initialize_continuation_simulation
from stock_cn.research_execution import settle_locked_research_decision
from stock_cn.sim_variants import VariantSimulation
from stock_cn.simulation import read_json


def add_future_session(data):
    out = copy.deepcopy(data)
    day = "2025-08-11"
    out["sessions"] = list(out["sessions"]) + [day]
    out["bars"][day] = {
        "600036.SH": {
            "open": "41.10",
            "close": "41.20",
            "high": "41.30",
            "low": "41.00",
            "volume": "160000",
            "source": "TEST_ONLY:continuation",
            "suspended": False,
            "limit_up": "45.10",
            "limit_down": "36.90",
        }
    }
    return out


def test_continuation_preserves_settled_cash_positions_and_cost(repo):
    data, _, _ = prepare_locked(repo, "continuation-source", target="2025-08-07")
    settlement = settle_locked_research_decision(
        repo, "continuation-source", "D02", "2025-08-07",
        data, check_through="2025-08-08",
    )
    assert settlement["execution"]["status"] == "FILLED"

    formal_before = read_json(repo / "strategies/D/variants/D02/holdings.json")
    future = add_future_session(data)
    cont_path = (
        "runs/research-decisions/continuation-source/D02/2025-08-07/"
        "continuation.json"
    )
    state = initialize_continuation_simulation(
        repo, "D02", "continuation-run", future, cont_path
    )
    source = settlement["holdings_after"]
    assert state["cash_cny"] == source["cash_cny"]
    assert state["total_equity_cny"] == source["total_equity_cny"]
    assert state["positions"][0]["quantity"] == source["positions"][0]["quantity"]
    assert state["positions"][0]["average_cost_cny"] == source["positions"][0]["average_cost_cny"]
    assert state["_meta"]["source_decision_sha256"] == settlement["decision_sha256"]
    assert read_json(repo / "strategies/D/variants/D02/holdings.json") == formal_before


def test_continuation_next_day_prompt_uses_carried_account(repo):
    data, _, _ = prepare_locked(repo, "continuation-prompt-source", target="2025-08-07")
    settlement = settle_locked_research_decision(
        repo, "continuation-prompt-source", "D02", "2025-08-07",
        data, check_through="2025-08-08",
    )
    future = add_future_session(data)
    cont_path = (
        "runs/research-decisions/continuation-prompt-source/D02/2025-08-07/"
        "continuation.json"
    )
    initialize_continuation_simulation(
        repo, "D02", "continuation-prompt-run", future, cont_path
    )
    sim = VariantSimulation(repo, "D", "D02", "continuation-prompt-run", future)
    req = sim.prepare("2025-08-11")
    assert req["holdings"]["positions"][0]["quantity"] == 100
    assert req["holdings"]["cash_cny"] == settlement["holdings_after"]["cash_cny"]
    assert "CONTINUATION_FROM_LOCKED_RESEARCH_DECISION" in (
        sim.store.path("manifest.json").read_text(encoding="utf-8")
    )


def test_continuation_is_idempotent_for_same_source(repo):
    data, _, _ = prepare_locked(repo, "continuation-idem-source", target="2025-08-07")
    settle_locked_research_decision(
        repo, "continuation-idem-source", "D02", "2025-08-07",
        data, check_through="2025-08-08",
    )
    future = add_future_session(data)
    cont_path = (
        "runs/research-decisions/continuation-idem-source/D02/2025-08-07/"
        "continuation.json"
    )
    first = initialize_continuation_simulation(
        repo, "D02", "continuation-idem-run", future, cont_path
    )
    second = initialize_continuation_simulation(
        repo, "D02", "continuation-idem-run", future, cont_path
    )
    assert first == second
