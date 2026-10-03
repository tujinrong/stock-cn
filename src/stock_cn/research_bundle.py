"""Compose point-in-time research evidence without turning coverage into a score.

The bundle tells the AI what is known, what was checked, and what remains missing.
It never labels a stock BUY/SELL and never treats missing data as favorable evidence.
"""
from __future__ import annotations

from datetime import datetime

from .evidence import (
    official_disclosure_status,
    validate_official_disclosure_pack,
)


def _aware(value, field):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(field + " must be timezone-aware")
    return dt


def _causal_items(items, cutoff, *, time_field="published_at"):
    out = []
    for item in items or []:
        if not isinstance(item, dict) or not item.get(time_field):
            raise ValueError("research evidence item missing time")
        when = _aware(item[time_field], time_field)
        if when > cutoff:
            raise ValueError("future research evidence")
        out.append(item)
    return out


def validate_financial_review(review, *, symbol, as_of):
    """Validate an AI-produced review of latest disclosed financial information."""
    if not isinstance(review, dict):
        raise ValueError("financial review must be an object")
    if review.get("status") != "REVIEWED":
        raise ValueError("financial review status must be REVIEWED")
    if review.get("symbol") not in (None, symbol):
        raise ValueError("financial review belongs to another symbol")
    cutoff = _aware(as_of, "as_of")
    review_time = _aware(review.get("as_of"), "financial review as_of")
    if review_time > cutoff:
        raise ValueError("future financial review")
    if not review.get("source_report"):
        raise ValueError("financial review source report missing")
    if review.get("source_official") is not True:
        raise ValueError("financial review must identify an official source")
    facts = review.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ValueError("financial review must contain at least one sourced fact")
    for fact in facts:
        if not isinstance(fact, dict):
            raise ValueError("financial fact must be an object")
        if not fact.get("name") or "value" not in fact or not fact.get("source"):
            raise ValueError("financial fact missing name/value/source")
    if not isinstance(review.get("data_gaps", []), list):
        raise ValueError("financial review data_gaps must be a list")
    return True


def validate_news_research(news, *, as_of, allowed_symbols):
    """Validate AI/web news-search provenance without judging sentiment."""
    if not isinstance(news, dict):
        raise ValueError("news research must be an object")
    status = news.get("status")
    if status not in {
        "SEARCHED", "NO_RELEVANT_RECENT_NEWS", "UNAVAILABLE", "NOT_CHECKED"
    }:
        raise ValueError("invalid news research status")
    cutoff = _aware(as_of, "as_of")
    searched_at = news.get("searched_at") or news.get("as_of")
    if searched_at:
        if _aware(searched_at, "news searched_at") > cutoff:
            raise ValueError("future news search timestamp")
    items = news.get("items", [])
    if not isinstance(items, list):
        raise ValueError("news items must be a list")
    if status == "NO_RELEVANT_RECENT_NEWS" and items:
        raise ValueError("NO_RELEVANT_RECENT_NEWS cannot contain items")
    allowed_symbols = set(allowed_symbols)
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("news item must be an object")
        if not item.get("title") or not item.get("source") or not item.get("published_at"):
            raise ValueError("news item missing title/source/published_at")
        if _aware(item["published_at"], "news published_at") > cutoff:
            raise ValueError("future research evidence: news")
        symbols = set(item.get("symbols", []))
        if not symbols <= allowed_symbols:
            raise ValueError("news item references symbol outside research bundle")
        if item.get("material_fact") is True and not item.get("official_recheck_status"):
            raise ValueError("material media fact must declare official recheck status")
    return True


def build_decision_research_bundle(
    symbols,
    *,
    as_of,
    official_disclosure_pack=None,
    candidate_research_pack=None,
    research_state=None,
    financial_reviews=None,
    news_research=None,
    market_context=None,
):
    """Build a causal research map for holdings/candidates at one decision time."""
    if not symbols or len(symbols) > 30:
        raise ValueError("research bundle requires 1..30 symbols")
    if len(symbols) != len(set(symbols)):
        raise ValueError("duplicate research symbols")
    cutoff = _aware(as_of, "as_of")

    if official_disclosure_pack is not None:
        validate_official_disclosure_pack(
            official_disclosure_pack, as_of=as_of, required_symbols=symbols
        )

    financial_reviews = financial_reviews or {}
    news_research = news_research or {"status": "NOT_CHECKED", "items": []}
    validate_news_research(news_research, as_of=as_of, allowed_symbols=symbols)
    latest_reports = {}
    important = {}
    if official_disclosure_pack:
        for item in official_disclosure_pack.get("latest_periodic_report_refs", []):
            latest_reports.setdefault(item["symbol"], item)
        for item in official_disclosure_pack.get("important_recent_refs", []):
            important.setdefault(item["symbol"], []).append(item)

    news_items = news_research.get("items", []) if isinstance(news_research, dict) else []
    news_items = _causal_items(news_items, cutoff)
    news_checked_through = news_research.get('searched_at') or news_research.get('as_of')
    news_checked_for_date = bool(news_checked_through and
        _aware(news_checked_through, 'news coverage time').astimezone(cutoff.tzinfo).date() == cutoff.date())
    historical_news_ignored = bool(market_context and market_context.get('mode') == 'SIMULATION' and
        market_context.get('historical_news_policy') == 'IGNORE_UNRELIABLE_ARCHIVED_NEWS')
    if historical_news_ignored:
        news_items = []
    news_by_symbol = {s: [] for s in symbols}
    for item in news_items:
        for symbol in item.get("symbols", []):
            if symbol in news_by_symbol:
                news_by_symbol[symbol].append(item)

    rows = []
    for symbol in symbols:
        disclosure_status = official_disclosure_status(
            official_disclosure_pack, symbol
        )
        report = latest_reports.get(symbol)
        financial = financial_reviews.get(symbol)
        if financial:
            validate_financial_review(financial, symbol=symbol, as_of=as_of)
            financial_status = "REVIEWED"
        elif report:
            financial_status = "REPORT_REFERENCE_AVAILABLE_REVIEW_REQUIRED"
        else:
            financial_status = "LATEST_REPORT_REFERENCE_MISSING"

        global_news_status = (
            news_research.get("status", "NOT_CHECKED")
            if isinstance(news_research, dict) else "NOT_CHECKED"
        )
        source_news_status = global_news_status
        if historical_news_ignored:
            global_news_status = 'IGNORED_HISTORICAL_NEWS'
        elif global_news_status in {'SEARCHED', 'NO_RELEVANT_RECENT_NEWS'} and not news_checked_for_date:
            global_news_status = 'ARCHIVED_CHECK_ONLY' if news_checked_through else 'CHECK_TIME_UNKNOWN'
        symbol_news = sorted(
            news_by_symbol.get(symbol, []),
            key=lambda x: x["published_at"],
            reverse=True,
        )
        gaps = []
        if disclosure_status == "FAILED":
            gaps.append("OFFICIAL_DISCLOSURE_PROVIDER_FAILED")
        elif disclosure_status == "NOT_CHECKED":
            gaps.append("OFFICIAL_DISCLOSURE_NOT_CHECKED")
        if report is None:
            gaps.append("LATEST_PERIODIC_REPORT_REFERENCE_MISSING")
        if financial_status != "REVIEWED":
            gaps.append("FINANCIAL_INTERPRETATION_NOT_COMPLETED")
        if global_news_status not in {"SEARCHED", "NO_RELEVANT_RECENT_NEWS"}:
            gaps.append("RECENT_NEWS_NOT_VERIFIED")

        rows.append({
            "symbol": symbol,
            "official_disclosure_status": disclosure_status,
            "latest_periodic_report_ref": report,
            "important_official_disclosures": important.get(symbol, [])[:8],
            "financial_review": financial,
            "financial_review_status": financial_status,
            "recent_news_status": global_news_status,
            "source_news_status": source_news_status,
            "news_coverage_through": news_checked_through,
            "news_checked_for_cutoff_date": news_checked_for_date and not historical_news_ignored,
            "recent_news_items": symbol_news[:8],
            "data_gaps": gaps,
            "no_investment_conclusion": True,
        })

    candidate_symbols = []
    if isinstance(candidate_research_pack, dict):
        candidate_symbols = [
            x.get("symbol") for x in candidate_research_pack.get("candidates", [])
            if x.get("symbol")
        ]
    held_or_researched = set(symbols)
    if not set(candidate_symbols) <= held_or_researched:
        raise ValueError("candidate pack contains symbol outside research bundle")

    coverage = {
        "official_ok_or_empty": sum(
            x["official_disclosure_status"] in {"OK", "EMPTY"} for x in rows
        ),
        "financial_interpretation_completed": sum(
            x["financial_review_status"] == "REVIEWED" for x in rows
        ),
        "news_verified": sum(
            x["recent_news_status"] in {"SEARCHED", "NO_RELEVANT_RECENT_NEWS"}
            for x in rows
        ),
        "symbol_count": len(rows),
    }
    return {
        "kind": "DECISION_RESEARCH_BUNDLE",
        "as_of": as_of,
        "symbols": list(symbols),
        "candidate_research_pack": candidate_research_pack,
        "research_state": research_state,
        "market_context": market_context,
        "per_symbol": rows,
        "coverage": coverage,
        "coverage_is_not_a_score": True,
        "research_rules": [
            "Missing or failed evidence is a data gap, never favorable evidence.",
            "Official disclosure metadata is a reference; financial conclusions require review of the actual disclosed information.",
            "News/media is a lead source. Material facts should be checked against official disclosure when possible.",
            "The AI decides relevance and synthesis; this bundle does not rank securities or dictate a trade.",
        ],
    }


def buy_research_preflight(bundle, symbol):
    """Return a structured preflight; caller decides whether BUY may proceed.

    This is deliberately narrow: official disclosure query must have succeeded,
    and recent news must have been checked. Financial interpretation may still
    contain declared gaps for the AI to resolve before returning READY.
    """
    if not isinstance(bundle, dict) or bundle.get("kind") != "DECISION_RESEARCH_BUNDLE":
        return {
            "ready": False,
            "reasons": ["DECISION_RESEARCH_BUNDLE_MISSING"],
        }
    row = next((x for x in bundle.get("per_symbol", []) if x.get("symbol") == symbol), None)
    if row is None:
        return {"ready": False, "reasons": ["SYMBOL_RESEARCH_MISSING"]}
    reasons = []
    if row["official_disclosure_status"] not in {"OK", "EMPTY"}:
        reasons.append("OFFICIAL_DISCLOSURE_NOT_SUCCESSFULLY_CHECKED")
    context = bundle.get('market_context') or {}
    ignored_historical = (row['recent_news_status'] == 'IGNORED_HISTORICAL_NEWS' and
                          context.get('mode') == 'SIMULATION' and
                          context.get('historical_news_policy') == 'IGNORE_UNRELIABLE_ARCHIVED_NEWS')
    if row["recent_news_status"] not in {"SEARCHED", "NO_RELEVANT_RECENT_NEWS"} and not ignored_historical:
        reasons.append("RECENT_NEWS_NOT_VERIFIED")
    if row["latest_periodic_report_ref"] is None and row["financial_review"] is None:
        reasons.append("LATEST_FINANCIAL_REFERENCE_MISSING")
    if row["financial_review_status"] != "REVIEWED":
        reasons.append("FINANCIAL_REVIEW_NOT_COMPLETED")
    return {
        "ready": not reasons,
        "reasons": reasons,
        "financial_review_status": row["financial_review_status"],
        "data_gaps": row["data_gaps"],
    }
