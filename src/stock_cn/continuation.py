"""Start an isolated continuous simulation from a settled research decision.

This preserves cash, positions and cost basis from the locked-decision settlement.
It never copies anything into FORMAL holdings and never resets the account to the
strategy's original 200k initialization.
"""
from __future__ import annotations

import copy
from pathlib import Path

from .sim_variants import VariantSimulation
from .simulation import holdings_md, read_json, require


def initialize_continuation_simulation(
    repo,
    variant,
    test_id,
    data,
    continuation_file,
):
    repo = Path(repo).resolve()
    continuation_file = Path(continuation_file)
    if not continuation_file.is_absolute():
        continuation_file = repo / continuation_file
    require(continuation_file.exists(), "continuation file missing")
    continuation = read_json(continuation_file)

    require(continuation.get("variant_id") == variant,
            "continuation belongs to another variant")
    require(continuation.get("formal_execution") is False,
            "FORMAL continuation cannot initialize a simulation")
    source_state = continuation.get("state")
    require(isinstance(source_state, dict), "continuation state missing")
    require(source_state.get("_meta", {}).get("mode") == "SIMULATION",
            "continuation state is not simulation")
    require(source_state.get("date") == continuation.get("execution_date"),
            "continuation state/execution date mismatch")
    require(source_state.get("_meta", {}).get("locked_research_decision") is True,
            "continuation is not from a locked research decision")
    require(continuation.get("execution_status") in {"FILLED", "NO_TRADE", "REJECTED"},
            "continuation execution status is not final")

    sim = VariantSimulation(repo, variant[0], variant, test_id, data)
    require(source_state["date"] in data["sessions"],
            "continuation date missing from supplied future dataset")
    for p in source_state.get("positions", []):
        require(p["symbol"] in data["instruments"],
                "continuation holding missing instrument metadata")
        require(p["symbol"] in data["bars"].get(source_state["date"], {}),
                "continuation holding missing source-day market data")

    with sim.store.lock():
        if sim.store.events():
            first = sim.store.events()[0]["documents"]["manifest.json"]
            require(first.get("initialization") ==
                    "CONTINUATION_FROM_LOCKED_RESEARCH_DECISION",
                    "existing simulation was initialized another way")
            require(first.get("source_decision_sha256") ==
                    continuation.get("decision_sha256"),
                    "existing continuation belongs to another decision")
            require(first.get("input_fingerprint") == sim._private_fingerprint,
                    "continuation inputs changed; use a new test_id")
            return sim.store.load()

        state = copy.deepcopy(source_state)
        state["status"] = "SIMULATION"
        state["strategy_id"] = variant[0]
        state["_meta"] = copy.deepcopy(state["_meta"])
        state["_meta"].update({
            "mode": "SIMULATION",
            "paper_only": True,
            "variant_id": variant,
            "test_id": test_id,
            "revision": 0,
            "continuation_source": str(continuation_file.relative_to(repo)),
            "source_decision_sha256": continuation["decision_sha256"],
            "source_execution_status": continuation["execution_status"],
        })

        manifest = {
            "mode": "SIMULATION",
            "submode": "CONTINUATION",
            "series": variant[0],
            "variant": variant,
            "test_id": test_id,
            "initialization": "CONTINUATION_FROM_LOCKED_RESEARCH_DECISION",
            "source_continuation": str(continuation_file.relative_to(repo)),
            "source_decision_sha256": continuation["decision_sha256"],
            "source_execution_date": continuation["execution_date"],
            "source_execution_status": continuation["execution_status"],
            "input_fingerprint": sim._private_fingerprint,
            "source_commit": sim.source_commit,
            "fees": {k: str(v) for k, v in sim.fees.items()},
            "data_kind": data["kind"],
            "fidelity": data["fidelity"],
            "formal_state_changed": False,
            "no_capital_reset": True,
            "limitations": data.get("limitations", []),
        }
        return sim.store.commit(
            "OPENING_BALANCE",
            None,
            state,
            {
                "manifest.json": manifest,
                "continuation.snapshot.json": continuation,
                "holdings_at_continuation.md": holdings_md(state),
            },
            {
                "source": "LOCKED_RESEARCH_DECISION_CONTINUATION",
                "decision_sha256": continuation["decision_sha256"],
            },
        )
