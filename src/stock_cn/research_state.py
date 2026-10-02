"""Durable AI_SELECT research-state management.

Research state is not an order, not a holding, and not a recommendation. Historical
and simulation runs keep their state inside the isolated simulation directory.
FORMAL state lives next to the variant prompt but can only be updated through an
explicitly-authorized path.
"""
from __future__ import annotations

import copy
from pathlib import Path

from .simulation import Store, digest, read_json, require
from .variant_prompts import variant_root, write


def default_state(series_id, variant_id, *, mode):
    require(mode in {"SIMULATION", "FORMAL"}, "invalid research-state mode")
    return {
        "variant_id": variant_id,
        "series_id": series_id,
        "mode": mode,
        "status": "NOT_STARTED",
        "date": None,
        "revision": 0,
        "candidate_watchlist": [],
        "last_candidate_pack": None,
        "last_broad_universe_source": None,
        "formal_research_enabled": False if mode == "FORMAL" else None,
        "last_decision_summary": None,
        "note": (
            "AI_SELECT research state only; never an order, holding or recommendation. "
            "Simulation state is isolated from FORMAL."
        ),
    }


def validate_state(state, *, series_id=None, variant_id=None, mode=None):
    require(isinstance(state, dict), "research state must be an object")
    require(isinstance(state.get("revision"), int) and state["revision"] >= 0,
            "invalid research-state revision")
    require(isinstance(state.get("candidate_watchlist"), list),
            "candidate_watchlist must be a list")
    require(state.get("mode") in {"SIMULATION", "FORMAL"}, "invalid research-state mode")
    if series_id is not None:
        require(state.get("series_id") == series_id, "research state belongs to another series")
    if variant_id is not None:
        require(state.get("variant_id") == variant_id, "research state belongs to another variant")
    if mode is not None:
        require(state.get("mode") == mode, "research state belongs to another mode")
    return True


def simulation_state_path(simulation_root):
    return Path(simulation_root) / "research_state.json"


def load_simulation_state(simulation_root, series_id, variant_id):
    p = simulation_state_path(simulation_root)
    if not p.exists():
        return default_state(series_id, variant_id, mode="SIMULATION")
    state = read_json(p)
    validate_state(state, series_id=series_id, variant_id=variant_id, mode="SIMULATION")
    return state


def sync_simulation_state(
    simulation_root,
    series_id,
    variant_id,
    cutoff_date,
    *,
    candidate_pack=None,
    watchlist=None,
    universe_scope=None,
    broad_source=None,
):
    """Persist one causal AI_SELECT research snapshot into an isolated simulation.

    Repeating the same input is idempotent. A different research pack for the same
    cutoff date requires a new test_id rather than silently rewriting history.
    """
    root = Path(simulation_root)
    store = Store(root)
    state = load_simulation_state(root, series_id, variant_id)
    payload = {
        "cutoff_date": cutoff_date,
        "candidate_pack": candidate_pack,
        "watchlist": watchlist,
        "universe_scope": universe_scope,
        "broad_source": broad_source,
    }
    payload_hash = digest(payload)

    existing = state.get("last_research_payload_sha256")
    if state.get("date") == cutoff_date and existing:
        require(existing == payload_hash,
                "research inputs changed for the same cutoff; use a new test_id")
        return state

    next_state = copy.deepcopy(state)
    next_state["date"] = cutoff_date
    next_state["revision"] = state["revision"] + 1
    next_state["status"] = "RESEARCH_READY" if candidate_pack else "NO_CANDIDATE_PACK"
    next_state["last_research_payload_sha256"] = payload_hash
    next_state["last_candidate_pack"] = None
    next_state["last_broad_universe_source"] = broad_source
    next_state["universe_scope"] = universe_scope
    if watchlist is not None:
        next_state["candidate_watchlist"] = copy.deepcopy(
            watchlist.get("candidate_watchlist", watchlist if isinstance(watchlist, list) else [])
        )

    research_dir = f"research/{cutoff_date}"
    if candidate_pack is not None:
        pack_hash = digest(candidate_pack)
        store.write(f"{research_dir}/candidate_pack.json", candidate_pack)
        next_state["last_candidate_pack"] = {
            "path": f"{research_dir}/candidate_pack.json",
            "sha256": pack_hash,
            "kind": candidate_pack.get("kind"),
            "purpose": candidate_pack.get("purpose"),
            "candidate_count": candidate_pack.get("selected_count"),
            "not_a_recommendation": candidate_pack.get("not_a_recommendation", True),
        }
    if watchlist is not None:
        store.write(f"{research_dir}/watchlist.json", watchlist)
    store.write(f"{research_dir}/universe_scope.json", universe_scope or {})
    store.write("research_state.json", next_state)
    return next_state


def formal_state_path(repo, variant_id):
    return variant_root(repo, variant_id) / "research_state.json"


def load_formal_state(repo, series_id, variant_id):
    p = formal_state_path(repo, variant_id)
    if not p.exists():
        return default_state(series_id, variant_id, mode="FORMAL")
    state = read_json(p)
    # Legacy materialization omitted mode. Normalize in memory, do not mutate here.
    if "mode" not in state:
        state = copy.deepcopy(state)
        state["mode"] = "FORMAL"
    validate_state(state, series_id=series_id, variant_id=variant_id, mode="FORMAL")
    return state


def update_formal_state(
    repo,
    series_id,
    variant_id,
    new_state,
    *,
    authorized=False,
):
    """Guarded FORMAL research-state write.

    This does not authorize trading. It is separate from holdings and formal prompt
    approval and requires explicit authorization from the caller.
    """
    require(authorized is True, "explicit authorization required for FORMAL research-state write")
    current = load_formal_state(repo, series_id, variant_id)
    require(current.get("formal_research_enabled") is True,
            "FORMAL research state is not enabled for this variant")
    candidate = copy.deepcopy(new_state)
    candidate["series_id"] = series_id
    candidate["variant_id"] = variant_id
    candidate["mode"] = "FORMAL"
    candidate["revision"] = current["revision"] + 1
    candidate["formal_research_enabled"] = True
    validate_state(candidate, series_id=series_id, variant_id=variant_id, mode="FORMAL")
    write(formal_state_path(repo, variant_id), candidate)
    return candidate
