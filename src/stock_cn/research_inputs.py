"""Load auditable decision research inputs from repository files.

This module bridges file-managed AI research and the runtime decision snapshot.
It never mutates holdings, prompts, research state or execution authorization.
"""
from __future__ import annotations

import copy
from datetime import datetime
from pathlib import Path

from .evidence import validate_official_disclosure_pack
from .research_bundle import validate_financial_review, validate_news_research
from .simulation import digest, read_json, require, identifier


FILENAMES = {
    "official_disclosure_pack": "official-disclosure-pack.json",
    "financial_reviews": "financial-reviews.json",
    "news_research": "news-research.json",
    "candidate_research_pack": "candidate-research-pack.json",
    "universe_scope": "universe-scope.json",
}


def research_input_root(repo, variant_id, decision_date, *, namespace=None):
    repo = Path(repo).resolve()
    if not isinstance(variant_id, str) or len(variant_id) != 3:
        raise ValueError("invalid variant identifier")
    datetime.fromisoformat(decision_date)
    base = repo / 'research-inputs'
    if namespace is not None:
        base = base / identifier(namespace)
    root = base / variant_id / decision_date
    if not root.resolve().is_relative_to((repo / "research-inputs").resolve()):
        raise ValueError("research input path escape")
    return root


def _aware(value, field):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(field + " must be timezone-aware")
    return dt


def _candidate_symbols(pack):
    if not isinstance(pack, dict):
        return set()
    return {
        x.get("symbol") for x in pack.get("candidates", [])
        if isinstance(x, dict) and x.get("symbol")
    }


def load_research_inputs(repo, variant_id, decision_date, *, as_of, namespace=None):
    """Load and validate one variant/day research-input directory.

    Missing optional files remain explicit None/NOT_CHECKED inputs. The caller may
    still prepare a SELL/HOLD decision, while BUY preflight can reject incomplete
    evidence later.
    """
    root = research_input_root(repo, variant_id, decision_date, namespace=namespace)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise ValueError("research input manifest missing")
    manifest = read_json(manifest_path)
    if manifest.get("variant_id") != variant_id:
        raise ValueError("research input belongs to another variant")
    if manifest.get("decision_date") != decision_date:
        raise ValueError("research input decision date mismatch")
    if manifest.get("mode") not in {"SIMULATION", "FORMAL"}:
        raise ValueError("research input mode invalid")

    cutoff = _aware(as_of, "decision as_of")
    manifest_cutoff = _aware(manifest.get("information_cutoff"), "research information_cutoff")
    if manifest_cutoff > cutoff:
        raise ValueError("research input comes from the future")

    values = {}
    hashes = {"manifest.json": digest(manifest)}
    for key, filename in FILENAMES.items():
        p = root / filename
        values[key] = read_json(p) if p.exists() else None
        if p.exists():
            hashes[filename] = digest(values[key])

    official = values["official_disclosure_pack"]
    if official is not None:
        validate_official_disclosure_pack(official, as_of=as_of)

    financials = values["financial_reviews"] or {}
    if not isinstance(financials, dict):
        raise ValueError("financial-reviews.json must be an object")
    for symbol, review in financials.items():
        validate_financial_review(review, symbol=symbol, as_of=as_of)

    candidate_pack = values["candidate_research_pack"]
    candidate_symbols = _candidate_symbols(candidate_pack)
    scope = values["universe_scope"]
    authorized_symbols = set()
    if scope is not None:
        if not isinstance(scope, dict):
            raise ValueError("universe-scope.json must be an object")
        authorized_symbols = set(scope.get("authorized_symbols") or [])
        if candidate_symbols and not candidate_symbols <= authorized_symbols:
            raise ValueError("candidate pack contains symbol outside authorized universe")

    allowed_symbols = set(financials) | candidate_symbols | authorized_symbols
    if official is not None:
        allowed_symbols |= set(official.get("symbols_requested") or [])
        allowed_symbols |= {x.get("symbol") for x in official.get("results", []) if x.get("symbol")}

    news = values["news_research"]
    if news is None:
        news = {"status": "NOT_CHECKED", "items": []}
    validate_news_research(news, as_of=as_of, allowed_symbols=allowed_symbols)

    return {
        "kind": "FILE_RESEARCH_INPUT_BUNDLE",
        "variant_id": variant_id,
        "decision_date": decision_date,
        "mode": manifest["mode"],
        "information_cutoff": manifest["information_cutoff"],
        "source_commit": manifest.get("source_commit"),
        "formal_execution": manifest.get("formal_execution", False),
        "path": str(root.relative_to(Path(repo).resolve())),
        "file_sha256": hashes,
        "official_disclosure_pack": official,
        "financial_reviews": financials,
        "news_research": news,
        "candidate_research_pack": candidate_pack,
        "universe_scope": scope,
        "missing_files": [
            filename for key, filename in FILENAMES.items()
            if values[key] is None
        ],
        "research_only": True,
    }


def attach_research_inputs(snapshot, bundle):
    """Attach validated file inputs to a runtime snapshot without silent override."""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    if bundle.get("kind") != "FILE_RESEARCH_INPUT_BUNDLE":
        raise ValueError("invalid file research input bundle")
    if snapshot.get("market_date") != bundle.get("decision_date"):
        raise ValueError("research input date does not match snapshot")
    snap = copy.deepcopy(snapshot)
    mapping = {
        "official_disclosure_pack": bundle.get("official_disclosure_pack"),
        "financial_reviews": bundle.get("financial_reviews"),
        "news_research": bundle.get("news_research"),
        "candidate_research_pack": bundle.get("candidate_research_pack"),
        "universe_scope": bundle.get("universe_scope"),
    }
    for key, value in mapping.items():
        if value is None:
            continue
        if key in snap and snap[key] != value:
            raise ValueError("runtime snapshot conflicts with file research input: " + key)
        snap[key] = value
    snap["research_input_manifest"] = {
        "variant_id": bundle["variant_id"],
        "path": bundle["path"],
        "information_cutoff": bundle["information_cutoff"],
        "file_sha256": bundle["file_sha256"],
        "missing_files": bundle["missing_files"],
    }
    return snap
