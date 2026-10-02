import json
from pathlib import Path

import pytest

from stock_cn.research_state import (
    default_state,
    load_formal_state,
    load_simulation_state,
    sync_simulation_state,
    update_formal_state,
)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pack(day="2026-09-30"):
    return {
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": "LOW_RECOVERY",
        "cutoff_date": day,
        "selected_count": 1,
        "not_a_recommendation": True,
        "candidates": [{"symbol": "600036.SH", "name": "招商银行"}],
    }


def watch(day="2026-09-30"):
    return {
        "kind": "ABNORMAL_DROP_RESEARCH_WATCHLIST",
        "date": day,
        "revision": 1,
        "candidate_watchlist": [{
            "symbol": "600900.SH", "name": "长江电力",
            "research_state": "FRESH_DROP_MONITOR",
            "not_a_trade_signal": True,
        }],
        "not_a_recommendation": True,
    }


def test_simulation_research_state_is_isolated_and_idempotent(tmp_path):
    root = tmp_path / "strategies/D/variants/D02/simulations/test-one"
    state = sync_simulation_state(
        root, "D", "D02", "2026-09-30",
        candidate_pack=pack(),
        watchlist=watch(),
        universe_scope={
            "authorized_symbols": ["600036.SH"],
            "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
        },
        broad_source={"provider": "Sina", "fallback_used": True},
    )
    assert state["mode"] == "SIMULATION"
    assert state["revision"] == 1
    assert state["candidate_watchlist"][0]["symbol"] == "600900.SH"
    assert state["last_candidate_pack"]["candidate_count"] == 1
    assert (root / "research/2026-09-30/candidate_pack.json").exists()

    again = sync_simulation_state(
        root, "D", "D02", "2026-09-30",
        candidate_pack=pack(),
        watchlist=watch(),
        universe_scope={
            "authorized_symbols": ["600036.SH"],
            "coverage": "BOUNDED_RESEARCH_CANDIDATES_ONLY",
        },
        broad_source={"provider": "Sina", "fallback_used": True},
    )
    assert again == state
    assert load_simulation_state(root, "D", "D02")["revision"] == 1

    changed = pack()
    changed["candidates"].append({"symbol": "600900.SH", "name": "长江电力"})
    changed["selected_count"] = 2
    with pytest.raises(ValueError, match="new test_id"):
        sync_simulation_state(
            root, "D", "D02", "2026-09-30",
            candidate_pack=changed,
            universe_scope={"authorized_symbols": ["600036.SH", "600900.SH"]},
        )


def test_simulation_research_state_advances_only_on_new_cutoff(tmp_path):
    root = tmp_path / "sim"
    first = sync_simulation_state(root, "F", "F01", "2026-09-30",
                                  candidate_pack=pack(), watchlist=watch())
    second_pack = pack("2026-10-08")
    second = sync_simulation_state(
        root, "F", "F01", "2026-10-08",
        candidate_pack=second_pack,
        watchlist=watch("2026-10-08"),
    )
    assert first["revision"] == 1
    assert second["revision"] == 2
    assert second["date"] == "2026-10-08"


def test_formal_research_state_write_requires_separate_authorization(tmp_path):
    root = tmp_path / "strategies/D/variants/D02"
    initial = default_state("D", "D02", mode="FORMAL")
    write(root / "research_state.json", initial)

    loaded = load_formal_state(tmp_path, "D", "D02")
    assert loaded["formal_research_enabled"] is False
    with pytest.raises(ValueError, match="authorization"):
        update_formal_state(tmp_path, "D", "D02", loaded, authorized=False)
    with pytest.raises(ValueError, match="not enabled"):
        update_formal_state(tmp_path, "D", "D02", loaded, authorized=True)

    initial["formal_research_enabled"] = True
    write(root / "research_state.json", initial)
    candidate = dict(initial)
    candidate["date"] = "2026-10-08"
    candidate["status"] = "RESEARCH_READY"
    updated = update_formal_state(tmp_path, "D", "D02", candidate, authorized=True)
    assert updated["revision"] == 1
    assert updated["date"] == "2026-10-08"
    assert updated["mode"] == "FORMAL"
