"""Bounded A-share universe discovery for AI_SELECT strategies.

This module is a research pre-filter, never an investment rule. It reduces a broad
A-share list to a bounded candidate set before deeper point-in-time K-line analysis.
STAR Market is excluded. Current project constraints also exclude unsupported
ChiNext/unknown boards until explicitly enabled and tested.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .sim_data import number, request_json, validate_dataset
from .time_travel import symbol_snapshot

EASTMONEY_CLIST = "https://push2.eastmoney.com/api/qt/clist/get"
SINA_CLIST = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"

SH_MAIN_PREFIXES = ("600", "601", "603", "605")
SZ_MAIN_PREFIXES = ("000", "001", "002", "003")


def _eligible(code, market):
    if not isinstance(code, str) or len(code) != 6:
        return False
    if market == 1:
        return code.startswith(SH_MAIN_PREFIXES)
    if market == 0:
        return code.startswith(SZ_MAIN_PREFIXES)
    return False


def _symbol(code, market):
    return code + (".SH" if market == 1 else ".SZ")


def _sina_request_json(url, timeout=15):
    req = Request(url, headers={
        "User-Agent": "stock-cn-universe/0.5",
        "Referer": "https://vip.stock.finance.sina.com.cn/",
    })
    with urlopen(req, timeout=timeout) as response:
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("sina response size limit exceeded")
    return json.loads(raw.decode("utf-8"))


def _row_from_eastmoney(row):
    code = str(row.get("f12", ""))
    try:
        market = int(row.get("f13"))
    except (TypeError, ValueError):
        return None
    if not _eligible(code, market):
        return None
    name = str(row.get("f14") or "").strip()
    if not name:
        return None
    def dec(key):
        value = row.get(key)
        if value in (None, "", "-"):
            return None
        try:
            return str(number(value))
        except ValueError:
            return None
    return {
        "symbol": _symbol(code, market),
        "name": name,
        "price_cny": dec("f2"),
        "change_pct": dec("f3"),
        "amount_cny": dec("f6"),
        "turnover_rate_pct": dec("f8"),
        "market_cap_cny": dec("f20"),
        "float_market_cap_cny": dec("f21"),
        "source_provider": "Eastmoney",
        "risk_tags": [tag for tag, cond in (
            ("ST_NAME", "ST" in name.upper()),
            ("SPECIAL_NAME", name.startswith(("N", "C"))),
        ) if cond],
    }


def _row_from_sina(row, market):
    code = str(row.get("code") or "").strip()
    if not _eligible(code, market):
        return None
    name = str(row.get("name") or "").strip()
    if not name:
        return None
    def dec(key):
        value = row.get(key)
        if value in (None, "", "-"):
            return None
        try:
            return str(number(value))
        except ValueError:
            return None
    return {
        "symbol": _symbol(code, market),
        "name": name,
        "price_cny": dec("trade"),
        "change_pct": dec("changepercent"),
        "amount_cny": dec("amount"),
        "turnover_rate_pct": dec("turnoverratio"),
        # Sina's mktcap/nmc unit convention is not treated as CNY here.
        "market_cap_cny": None,
        "float_market_cap_cny": None,
        "source_provider": "Sina",
        "risk_tags": [tag for tag, cond in (
            ("ST_NAME", "ST" in name.upper()),
            ("SPECIAL_NAME", name.startswith(("N", "C"))),
        ) if cond],
    }


def _fetch_sina_universe(request, *, page_size=80, max_pages=80):
    all_rows = {}
    pages = 0
    source_urls = []
    for node, market in (("sh_a", 1), ("sz_a", 0)):
        for page in range(1, max_pages + 1):
            url = SINA_CLIST + "?" + urlencode({
                "page": page, "num": page_size, "sort": "symbol",
                "asc": 1, "node": node, "_s_r_a": "page",
            })
            payload = request(url)
            if not isinstance(payload, list):
                raise ValueError("unexpected Sina universe payload")
            if not payload:
                break
            before = len(all_rows)
            for raw in payload:
                item = _row_from_sina(raw, market)
                if item:
                    all_rows[item["symbol"]] = item
            pages += 1
            source_urls.append(url)
            if len(payload) < page_size or len(all_rows) == before:
                break
    rows = list(all_rows.values())
    if len(rows) < 100:
        raise ValueError(f"unexpectedly small Sina universe: eligible={len(rows)} pages={pages}")
    return {
        "kind": "CURRENT_UNIVERSE_SNAPSHOT",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": SINA_CLIST,
        "source_provider": "Sina",
        "source_pages": pages,
        "source_last_url": source_urls[-1] if source_urls else None,
        "scope": "SH/SZ ordinary main-board prefixes supported by current project; STAR and unsupported boards excluded",
        "total_provider_rows": None,
        "raw_unique_rows": len(rows),
        "eligible_count": len(rows),
        "rows": rows,
    }


def fetch_live_universe(request=request_json, *, page_size=100, max_pages=60, fallback_request=None):
    """Fetch current broad A-share cross section with explicit provider fallback.

    Eastmoney is primary. If any paging request fails or returns an implausibly
    incomplete universe, the partial result is discarded and Sina is fetched from
    scratch. This is current discovery, not a historical universe archive.
    """
    if not 20 <= page_size <= 200 or not 1 <= max_pages <= 100:
        raise ValueError("invalid paging budget")
    eastmoney_error = None
    try:
        all_rows = {}
        total = None
        pages = 0
        source_urls = []
        for page in range(1, max_pages + 1):
            url = EASTMONEY_CLIST + "?" + urlencode({
                "pn": page, "pz": page_size, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                "fields": "f2,f3,f6,f8,f12,f13,f14,f20,f21",
            })
            payload = request(url)
            data = payload.get("data") or {}
            if total is None:
                total = data.get("total")
            diff = data.get("diff") or []
            if isinstance(diff, dict):
                page_rows = list(diff.values())
            elif isinstance(diff, list):
                page_rows = diff
            else:
                raise ValueError("unexpected Eastmoney universe payload")
            if not page_rows:
                break
            before = len(all_rows)
            for raw in page_rows:
                item = _row_from_eastmoney(raw)
                if item:
                    all_rows[item["symbol"]] = item
            pages += 1
            source_urls.append(url)
            if len(all_rows) == before:
                break
            if total is not None:
                try:
                    if page * page_size >= int(total):
                        break
                except (TypeError, ValueError):
                    pass
        rows = list(all_rows.values())
        if len(rows) < 100:
            raise ValueError(
                f"unexpectedly small Eastmoney universe: eligible={len(rows)} "
                f"total={total} pages={pages}"
            )
        return {
            "kind": "CURRENT_UNIVERSE_SNAPSHOT",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "source": EASTMONEY_CLIST,
            "source_provider": "Eastmoney",
            "source_pages": pages,
            "source_last_url": source_urls[-1] if source_urls else None,
            "scope": "SH/SZ ordinary main-board prefixes supported by current project; STAR and unsupported boards excluded",
            "total_provider_rows": total,
            "raw_unique_rows": len(rows),
            "eligible_count": len(rows),
            "rows": rows,
            "fallback_used": False,
        }
    except Exception as exc:
        eastmoney_error = f"{type(exc).__name__}: {exc}"[:800]

    fb = fallback_request
    if fb is None:
        fb = request if request is not request_json else _sina_request_json
    result = _fetch_sina_universe(fb)
    result["fallback_used"] = True
    result["primary_failure"] = eastmoney_error
    return result


def _rank_numeric(rows, key, reverse=True):
    valid = [r for r in rows if r.get(key) is not None]
    return sorted(valid, key=lambda r: number(r[key]), reverse=reverse)


def bounded_prefilter(snapshot, purpose, *, max_candidates=60):
    """Reduce thousands of names to a bounded research set.

    The result is only a compute-budget gate. AI must not treat inclusion/rank as a
    recommendation or as proof of quality. Untagged ordinary shares consume the
    research budget first; ST/new-listing/special-name rows are retained only as a
    tail fallback rather than silently deleted from the authorized market.
    """
    if snapshot.get("kind") != "CURRENT_UNIVERSE_SNAPSHOT":
        raise ValueError("current universe snapshot required")
    if type(max_candidates) is not int or not 10 <= max_candidates <= 100:
        raise ValueError("candidate budget must be 10..100")
    rows = [r for r in snapshot["rows"]
            if r.get("price_cny") is not None and r.get("amount_cny") is not None]
    clean = [r for r in rows if not r.get("risk_tags")]
    tagged = [r for r in rows if r.get("risk_tags")]

    def unique_take(groups):
        ordered, seen = [], set()
        for group in groups:
            for r in group:
                if r["symbol"] in seen:
                    continue
                ordered.append(r)
                seen.add(r["symbol"])
                if len(ordered) >= max_candidates:
                    return ordered
        return ordered

    if purpose == "LOW_RECOVERY":
        clean_liquid = _rank_numeric(clean, "amount_cny")[:max_candidates * 3]
        clean_sized = _rank_numeric(clean, "market_cap_cny")[:max_candidates * 3]
        tagged_liquid = _rank_numeric(tagged, "amount_cny")[:max_candidates]
        ordered = unique_take([clean_liquid, clean_sized, tagged_liquid])
    elif purpose == "ABNORMAL_DROP":
        clean_losers = _rank_numeric(clean, "change_pct", reverse=False)[:max_candidates * 2]
        clean_liquid = _rank_numeric(clean, "amount_cny")[:max_candidates * 2]
        tagged_losers = _rank_numeric(tagged, "change_pct", reverse=False)[:max_candidates]
        ordered = unique_take([clean_losers, clean_liquid, tagged_losers])
    else:
        raise ValueError("unknown prefilter purpose")
    return {
        "kind": "BOUNDED_CANDIDATE_SEED",
        "purpose": purpose,
        "max_candidates": max_candidates,
        "count": len(ordered),
        "source_retrieved_at": snapshot["retrieved_at"],
        "source": snapshot["source"],
        "source_provider": snapshot.get("source_provider"),
        "fallback_used": snapshot.get("fallback_used", False),
        "primary_failure": snapshot.get("primary_failure"),
        "not_a_recommendation": True,
        "risk_tag_policy": "UNTAGGED_FIRST; tagged rows only fill unused budget and remain visible if selected",
        "survivorship_warning": "Survivorship bias: this current universe snapshot must not be presented as a historically complete universe for past dates.",
        "rows": ordered,
    }


def _parse_history_rows(provider, payload, tx_symbol):
    if provider == "Tencent":
        return payload["data"][tx_symbol]["day"]
    return [x.split(",") for x in payload["data"]["klines"]]


def fetch_candidate_history(seed, start, end, request=request_json, *, max_symbols=60):
    """Fetch bounded raw daily history for candidate research.

    One request per candidate, Tencent first and Eastmoney fallback. No raw history
    needs to be committed to the repository.
    """
    date.fromisoformat(start)
    date.fromisoformat(end)
    if end < start or (date.fromisoformat(end) - date.fromisoformat(start)).days > 400:
        raise ValueError("invalid history interval")
    rows = seed.get("rows") or []
    if len(rows) > max_symbols:
        raise ValueError("candidate seed exceeds history budget")
    output, attempts, names = {}, [], {}
    for item in rows:
        symbol, name = item["symbol"], item["name"]
        code, exchange = symbol.split(".")
        if not _eligible(code, 1 if exchange == "SH" else 0):
            raise ValueError("unsupported candidate security")
        names[symbol] = name
        tx_symbol = exchange.lower() + code
        tx_url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urlencode({
            "param": f"{tx_symbol},day,{start},{end},320,"
        })
        em_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urlencode({
            "secid": f"{1 if exchange == 'SH' else 0}.{code}", "klt": 101, "fqt": 0,
            "beg": start.replace("-", ""), "end": end.replace("-", ""),
            "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57",
        })
        errors = []
        for provider, url in (("Tencent", tx_url), ("Eastmoney", em_url)):
            try:
                raw = _parse_history_rows(provider, request(url), tx_symbol)
                selected = {x[0]: {
                    "open": str(number(x[1])), "close": str(number(x[2])),
                    "high": str(number(x[3])), "low": str(number(x[4])),
                    "volume": str(number(x[5])) if len(x) > 5 and x[5] not in (None, "") else None,
                    "source": url, "provider": provider,
                } for x in raw if start <= x[0] <= end}
                if len(selected) < 2:
                    raise ValueError("insufficient returned sessions")
                output[symbol] = selected
                attempts.append({"symbol": symbol, "provider": provider, "status": "OK",
                                 "rows": len(selected), "fallback_errors": errors})
                break
            except Exception as exc:
                errors.append({"provider": provider, "error": f"{type(exc).__name__}: {exc}"[:400]})
        else:
            attempts.append({"symbol": symbol, "status": "FAILED", "errors": errors})
    good = [x for x in rows if x["symbol"] in output]
    if not good:
        return None, attempts

    sessions = sorted(set().union(*(set(x) for x in output.values())))
    tick = Decimal("0.01")
    for symbol, series in output.items():
        days = sorted(series)
        for i, day in enumerate(days):
            bar = series[day]
            bar["suspended"] = False
            if i == 0:
                bar["limit_up"] = None
                bar["limit_down"] = None
                continue
            prev = number(series[days[i-1]]["close"])
            cur = number(bar["close"])
            opened = number(bar["open"])
            if abs(cur / prev - 1) > Decimal("0.25") or abs(opened / prev - 1) > Decimal("0.25"):
                bar["limit_up"] = None
                bar["limit_down"] = None
                bar["limit_rule"] = "SUSPECTED_CORPORATE_ACTION_OR_DATA_BASIS_BREAK"
            else:
                bar["limit_up"] = str((prev * Decimal("1.10")).quantize(tick, rounding=ROUND_HALF_UP))
                bar["limit_down"] = str((prev * Decimal("0.90")).quantize(tick, rounding=ROUND_HALF_UP))
                bar["limit_rule"] = "ORDINARY_MAIN_BOARD_10PCT_FROM_PREVIOUS_CLOSE"

    dataset = {
        "schema_version": "0.4",
        "kind": "REAL_HISTORY",
        "price_basis": "unadjusted",
        "fidelity": "BOUNDED_CANDIDATE_REAL_DAILY",
        "sessions": sessions,
        "calendar_source": "union of returned candidate sessions; not independently certified",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Candidate set is bounded for compute control and is not a complete all-A-share research claim.",
            "No archived news/fundamentals/intraday verification in this adapter.",
            "Current-universe seeding has survivorship bias if reused for historical dates.",
            "Suspected >25% price-basis breaks are not assigned executable limit prices.",
        ],
        "instruments": {r["symbol"]: {
            "name": names[r["symbol"]], "board": "MAIN", "lot_size": 100,
            "price_limit_pct": "0.10",
        } for r in good},
        "bars": {d: {s: output[s][d] for s in output if d in output[s]} for d in sessions},
        "evidence": [],
        "corporate_actions": [],
    }
    validate_dataset(dataset)
    return dataset, attempts



def build_deep_research_pack(seed, dataset, cutoff_date, purpose, *, max_candidates=12):
    """Combine a bounded seed with causal K-line summaries for AI deep research.

    Labels are attention-routing states, never trade recommendations. They help
    keep prompts compact and make data gaps explicit.
    """
    date.fromisoformat(cutoff_date)
    if purpose not in {"LOW_RECOVERY", "ABNORMAL_DROP"}:
        raise ValueError("unknown research-pack purpose")
    if type(max_candidates) is not int or not 1 <= max_candidates <= 30:
        raise ValueError("deep-research budget must be 1..30")
    seed_rows = {x["symbol"]: x for x in seed.get("rows", [])}
    entries = []
    for symbol in dataset.get("instruments", {}):
        if symbol not in seed_rows:
            continue
        snap = symbol_snapshot(dataset, symbol, cutoff_date)
        if not snap:
            continue
        meta = seed_rows[symbol]
        risk_tags = list(meta.get("risk_tags") or [])
        structural_break = snap.get("suspected_price_basis_break")
        priority = 50
        state = "GENERAL_RESEARCH"
        reasons = []

        if structural_break:
            priority = 90
            state = "DATA_BASIS_BREAK_REVIEW"
            reasons.append("疑似除权/送转/价格口径断点，不能解释为经济性暴跌。")
        elif risk_tags:
            priority = 80
            state = "RISK_TAGGED_REVIEW"
            reasons.append("名称/上市状态含风险标签，先核查风险再谈交易。")
        elif purpose == "LOW_RECOVERY":
            ranges = snap["range_position_0_to_1"]
            available = [number(x) for x in (
                ranges.get("60_sessions"), ranges.get("120_sessions")
            ) if x is not None]
            low = bool(available) and min(available) <= Decimal("0.35")
            r5 = snap["returns_pct"].get("5_sessions")
            ma5 = snap["moving_average"].get("ma5")
            recovering = (
                r5 is not None and ma5 is not None
                and number(r5) > 0
                and number(snap["as_of_close"]) >= number(ma5)
            )
            if low and recovering:
                priority = 10
                state = "LOW_AND_EARLY_RECOVERY_RESEARCH"
                reasons.append("处于较低区间且短期价格已有初步回升迹象，值得AI深查质量与持续性。")
            elif low:
                priority = 20
                state = "LOW_WAITING_RECOVERY_RESEARCH"
                reasons.append("价格位置偏低，但当前价量尚不足以确认回升。")
            else:
                priority = 40
                state = "NOT_CLEARLY_LOW_RESEARCH"
                reasons.append("当前可见区间位置不属于明显低位，仅保留为对照候选。")
        else:
            chg = meta.get("change_pct")
            r5 = snap["returns_pct"].get("5_sessions")
            ma5 = snap["moving_average"].get("ma5")
            daily_drop = number(chg) if chg is not None else None
            if daily_drop is not None and daily_drop <= Decimal("-5"):
                if r5 is not None and ma5 is not None and number(r5) > 0 and number(snap["as_of_close"]) >= number(ma5):
                    priority = 15
                    state = "DROP_WITH_STABILIZATION_RESEARCH"
                    reasons.append("当日仍属明显下跌，但短周期已有部分稳定迹象；必须核查下跌原因，不能直接视为反转。")
                else:
                    priority = 20
                    state = "FRESH_DROP_MONITOR"
                    reasons.append("近期/当日明显下跌，尚无可信回升确认，适合进入观察池而不是立即抄底。")
            else:
                priority = 40
                state = "DROP_CONTEXT_RESEARCH"
                reasons.append("由异常下跌轻筛进入，但当前截面需由AI重新核对异常程度和原因。")

        entries.append({
            "symbol": symbol,
            "name": snap["name"],
            "research_state": state,
            "attention_priority": priority,
            "attention_reasons": reasons,
            "risk_tags": risk_tags,
            "seed_snapshot": {
                "price_cny": meta.get("price_cny"),
                "change_pct": meta.get("change_pct"),
                "amount_cny": meta.get("amount_cny"),
                "source_provider": meta.get("source_provider"),
            },
            "market_history": snap,
            "not_a_trade_signal": True,
        })

    entries.sort(key=lambda x: (x["attention_priority"], x["symbol"]))
    selected = entries[:max_candidates]
    return {
        "kind": "AI_SELECT_DEEP_RESEARCH_PACK",
        "purpose": purpose,
        "cutoff_date": cutoff_date,
        "candidate_budget": max_candidates,
        "selected_count": len(selected),
        "source_seed_count": seed.get("count"),
        "seed_source": seed.get("source"),
        "seed_provider": seed.get("source_provider"),
        "seed_fallback_used": seed.get("fallback_used", False),
        "not_a_recommendation": True,
        "selection_note": "attention_priority allocates AI research budget only; final BUY/SELL/HOLD comes from the variant full prompt.",
        "survivorship_warning": seed.get("survivorship_warning"),
        "candidates": selected,
    }



def update_abnormal_drop_watchlist(previous_state, seed, dataset, cutoff_date, *, max_entries=50):
    """Carry abnormal-drop candidates forward so recovery can be judged later.

    This is research state only. A watchlist status never authorizes or implies a
    trade. The initial drop day is deliberately MONITORING, not a buy point.
    """
    date.fromisoformat(cutoff_date)
    if type(max_entries) is not int or not 10 <= max_entries <= 100:
        raise ValueError("watchlist budget must be 10..100")
    previous_state = previous_state or {}
    old = {x["symbol"]: dict(x) for x in previous_state.get("candidate_watchlist", [])
           if isinstance(x, dict) and x.get("symbol")}
    seed_rows = {x["symbol"]: x for x in seed.get("rows", [])}
    symbols = set(old) | set(seed_rows)
    entries = []
    for symbol in sorted(symbols):
        snap = symbol_snapshot(dataset, symbol, cutoff_date) if symbol in dataset.get("instruments", {}) else None
        item = dict(old.get(symbol, {}))
        meta = seed_rows.get(symbol)
        if not item:
            item = {
                "symbol": symbol,
                "name": (meta or {}).get("name"),
                "origin_drop_date": cutoff_date,
                "origin_price_cny": (meta or {}).get("price_cny"),
                "origin_change_pct": (meta or {}).get("change_pct"),
                "risk_tags": list((meta or {}).get("risk_tags") or []),
                "first_seen_source": seed.get("source"),
            }
        item["last_review_date"] = cutoff_date
        if meta:
            item["last_cross_section_change_pct"] = meta.get("change_pct")
            item["last_cross_section_price_cny"] = meta.get("price_cny")
        if not snap:
            item["research_state"] = "DATA_UNAVAILABLE"
            item["recovery_evidence"] = []
            entries.append(item)
            continue
        item["last_close_cny"] = snap["as_of_close"]
        item["history_summary"] = {
            "returns_pct": snap["returns_pct"],
            "moving_average": snap["moving_average"],
            "range_position_0_to_1": snap["range_position_0_to_1"],
            "continuous_sessions": snap["continuous_analysis_sessions"],
            "suspected_price_basis_break": snap["suspected_price_basis_break"],
        }
        evidence = []
        if snap["suspected_price_basis_break"]:
            state = "DATA_BASIS_BREAK_REVIEW"
            evidence.append("存在疑似权益事件/价格口径断点。")
        elif item.get("risk_tags"):
            state = "RISK_TAGGED_REVIEW"
            evidence.append("存在风险名称/特殊上市状态标签。")
        elif item["origin_drop_date"] == cutoff_date:
            state = "FRESH_DROP_MONITOR"
            evidence.append("今天是异常下跌发现日；尚未经过后续交易日确认，不构成回升买点。")
        else:
            r5 = snap["returns_pct"].get("5_sessions")
            ma5 = snap["moving_average"].get("ma5")
            closes = [number(x["close"]) for x in snap["kline"]["daily_last20"]]
            no_new_low_last3 = len(closes) >= 4 and min(closes[-3:]) > min(closes[-4:])
            above_ma5 = ma5 is not None and number(snap["as_of_close"]) >= number(ma5)
            positive_5d = r5 is not None and number(r5) > 0
            if positive_5d:
                evidence.append("近5个交易日收益已转正。")
            if above_ma5:
                evidence.append("当前收盘不低于MA5。")
            if no_new_low_last3:
                evidence.append("最近3个收盘未再创前一观察窗口新低。")
            if positive_5d and above_ma5 and no_new_low_last3:
                state = "RECOVERY_CONFIRMATION_RESEARCH"
            elif above_ma5 or no_new_low_last3:
                state = "EARLY_STABILIZATION_RESEARCH"
            else:
                state = "MONITORING_DROP"
        item["research_state"] = state
        item["recovery_evidence"] = evidence
        item["not_a_trade_signal"] = True
        entries.append(item)

    rank = {
        "RECOVERY_CONFIRMATION_RESEARCH": 10,
        "EARLY_STABILIZATION_RESEARCH": 20,
        "FRESH_DROP_MONITOR": 30,
        "MONITORING_DROP": 40,
        "RISK_TAGGED_REVIEW": 80,
        "DATA_BASIS_BREAK_REVIEW": 90,
        "DATA_UNAVAILABLE": 95,
    }
    entries.sort(key=lambda x: (rank.get(x.get("research_state"), 70),
                                x.get("origin_drop_date") or "", x["symbol"]))
    entries = entries[:max_entries]
    return {
        "kind": "ABNORMAL_DROP_RESEARCH_WATCHLIST",
        "date": cutoff_date,
        "revision": int(previous_state.get("revision", 0)) + 1,
        "candidate_watchlist": entries,
        "not_a_recommendation": True,
        "rule": "Only the variant AI may convert researched recovery evidence into BUY/SELL/HOLD; watchlist state alone never trades.",
    }
