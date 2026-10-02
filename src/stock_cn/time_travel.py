"""Causal time-travel context built only from data visible at a historical cutoff.

The strategy prompt itself is unchanged. A runtime appendix tells the AI that it
has travelled back to a target date and supplies only point-in-time market data,
multi-timeframe K-lines and structural industry context. News is optional and is
ignored by default because archived news is often incomplete.
"""
from __future__ import annotations

import json
import math
import statistics
from collections import OrderedDict
from datetime import date
from decimal import Decimal

from .sim_data import number


INDUSTRY_PROFILES = {
    "600036.SH": {
        "industry": "银行",
        "characteristics": ["利率与净息差敏感", "资产质量与信用周期重要", "分红和资本充足率影响估值"],
    },
    "002594.SZ": {
        "industry": "新能源汽车/汽车制造",
        "characteristics": ["销量与单车盈利需同时看", "价格竞争与产品周期敏感", "海外扩张和资本开支影响现金流"],
    },
    "600660.SH": {
        "industry": "汽车零部件/汽车玻璃",
        "characteristics": ["汽车产销周期相关", "高附加值产品结构影响利润", "海外业务、汇率和能源成本可能影响盈利"],
    },
    "600900.SH": {
        "industry": "电力/水电",
        "characteristics": ["现金流和分红属性较强", "来水与发电量影响经营", "利率环境影响高股息资产估值"],
    },
    "601100.SH": {
        "industry": "工业机械/液压",
        "characteristics": ["工程机械与制造业资本开支相关", "周期性需求和出口重要", "产能利用率与产品结构影响利润率"],
    },
}


def _fmt(value):
    if value is None:
        return None
    return str(number(value).quantize(Decimal("0.0001")))


def _ohlcv(bar):
    o, c = number(bar["open"]), number(bar["close"])
    high = number(bar.get("high", max(o, c)))
    low = number(bar.get("low", min(o, c)))
    volume = bar.get("volume")
    return {
        "open": _fmt(o), "high": _fmt(high), "low": _fmt(low), "close": _fmt(c),
        "volume": None if volume is None else _fmt(volume),
        "source": bar.get("source"),
    }


def _aggregate(rows, key_func, limit):
    groups = OrderedDict()
    for day, bar in rows:
        key = key_func(day)
        groups.setdefault(key, []).append((day, bar))
    result = []
    for key, items in groups.items():
        first, last = items[0], items[-1]
        values = [_ohlcv(x[1]) for x in items]
        highs = [number(x["high"]) for x in values]
        lows = [number(x["low"]) for x in values]
        volumes = [number(x["volume"]) for x in values if x["volume"] is not None]
        result.append({
            "period": key, "start": first[0], "end": last[0],
            "open": values[0]["open"], "high": _fmt(max(highs)),
            "low": _fmt(min(lows)), "close": values[-1]["close"],
            "volume": _fmt(sum(volumes)) if volumes else None,
        })
    return result[-limit:]


def _ret(closes, periods):
    if len(closes) <= periods:
        return None
    a, b = closes[-periods-1], closes[-1]
    return _fmt((b / a - 1) * 100)


def _ma(closes, periods):
    if len(closes) < periods:
        return None
    return _fmt(sum(closes[-periods:]) / periods)


def _range_position(closes, periods):
    if len(closes) < 2:
        return None
    sample = closes[-min(periods, len(closes)):]
    lo, hi, cur = min(sample), max(sample), sample[-1]
    if hi == lo:
        return "0.5000"
    return _fmt((cur - lo) / (hi - lo))


def _vol(closes, periods=20):
    if len(closes) < 3:
        return None
    sample = closes[-min(periods + 1, len(closes)):]
    returns = [float(sample[i] / sample[i-1] - 1) for i in range(1, len(sample))]
    return _fmt(statistics.pstdev(returns) * math.sqrt(252) * 100) if returns else None


def symbol_snapshot(data, symbol, cutoff_date):
    rows = [(d, data["bars"][d][symbol]) for d in data["sessions"]
            if d <= cutoff_date and symbol in data["bars"].get(d, {})]
    if not rows:
        return None
    closes = [number(b["close"]) for _, b in rows]
    daily = [{"date": d, **_ohlcv(b)} for d, b in rows[-20:]]
    weekly = _aggregate(
        rows,
        lambda d: f"{date.fromisoformat(d).isocalendar().year}-W{date.fromisoformat(d).isocalendar().week:02d}",
        12,
    )
    monthly = _aggregate(rows, lambda d: d[:7], 12)
    meta = data["instruments"][symbol]
    profile = INDUSTRY_PROFILES.get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta["name"],
        "industry": meta.get("industry") or profile.get("industry"),
        "industry_characteristics": meta.get("industry_characteristics") or profile.get("characteristics", []),
        "as_of_close": _fmt(closes[-1]),
        "observations": len(rows),
        "returns_pct": {
            "5_sessions": _ret(closes, 5),
            "20_sessions": _ret(closes, 20),
            "60_sessions": _ret(closes, 60),
        },
        "moving_average": {"ma5": _ma(closes, 5), "ma20": _ma(closes, 20), "ma60": _ma(closes, 60)},
        "range_position_0_to_1": {
            "20_sessions": _range_position(closes, 20),
            "60_sessions": _range_position(closes, 60),
            "120_sessions": _range_position(closes, 120),
            "250_sessions": _range_position(closes, 250),
        },
        "annualized_volatility_pct_approx": _vol(closes),
        "kline": {"daily_last20": daily, "weekly_last12": weekly, "monthly_last12": monthly},
    }


def _universe_proxy(snapshots):
    valid = [s for s in snapshots if s]
    if not valid:
        return {}
    result = {
        "kind": "CONFIGURED_UNIVERSE_EQUAL_WEIGHT_PROXY_NOT_BROAD_MARKET_INDEX",
        "returns_pct": {},
    }
    for key in ("5_sessions", "20_sessions", "60_sessions"):
        vals = [Decimal(s["returns_pct"][key]) for s in valid if s["returns_pct"][key] is not None]
        result["returns_pct"][key] = None if not vals else _fmt(sum(vals) / len(vals))
    return result


def build_time_travel_context(data, target_date, cutoff_date, *, symbols=None, ignore_news=True, execution_date=None):
    """Build a point-in-time market view. No row after cutoff_date can enter output."""
    date.fromisoformat(target_date)
    date.fromisoformat(cutoff_date)
    if cutoff_date > target_date:
        raise ValueError("time-travel cutoff cannot be after target date")
    if execution_date is not None:
        date.fromisoformat(execution_date)
        if execution_date <= target_date:
            raise ValueError("daily time-travel execution must follow target date")
    symbols = list(symbols or data["instruments"].keys())
    snapshots = [symbol_snapshot(data, s, cutoff_date) for s in symbols if s in data["instruments"]]
    snapshots = [s for s in snapshots if s]
    return {
        "mode": "TIME_TRAVEL",
        "target_date": target_date,
        "knowledge_cutoff": cutoff_date + "T15:00:00+08:00",
        "planned_execution_date": execution_date,
        "instruction": (
            f"你现在回到{target_date}收盘时。请把自己视为当时的投资研究者。"
            f"你只能使用{cutoff_date}收盘及以前已经可见的市场资料，"
            "不知道之后任何价格、涨跌、财报结果或事件。不要用后验结果修正当时判断。"
            + (f" 本日线近似将在下一交易日{execution_date}开盘模拟执行。" if execution_date else "")
        ),
        "news_policy": "IGNORE_ARCHIVED_NEWS_BY_DEFAULT" if ignore_news else "USE_ONLY_POINT_IN_TIME_ARCHIVED_NEWS",
        "market_proxy": _universe_proxy(snapshots),
        "symbols": snapshots,
        "intraday_kline": {
            "status": "UNAVAILABLE_UNLESS_ARCHIVED_INTRADAY_DATA_IS_SUPPLIED",
            "rule": "不得用当日收盘或未来分钟线冒充历史盘中信息",
        },
        "limitations": [
            "行业特点为结构性研究背景，不代表当日行业消息。",
            "未提供真实大盘指数时，market_proxy只是本次可见股票池等权代理。",
            "日/周/月K线均由knowledge_cutoff以前的未复权历史日线聚合。",
            "新闻默认忽略；没有历史新闻不解释为当时没有新闻或风险。",
            "AI模型本身可能含有后来知识，因此仍不能声称完全消除前视偏差。",
        ],
    }


def append_time_travel_prompt(prompt, context):
    """Use the same complete strategy prompt, adding only a runtime travel appendix."""
    return (
        prompt.rstrip()
        + "\n\n## 时光穿越运行层（仅本次运行时注入，不改变策略正文）\n"
        + context["instruction"]
        + "\n\n下面数据均按knowledge_cutoff裁剪。把它们当作你在那个时点能看到的大致市场环境；"
          "新闻缺失可忽略，不允许根据后来的结果补全。\n\n"
        + json.dumps(context, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n"
    )
