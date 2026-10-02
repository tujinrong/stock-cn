from __future__ import annotations

from datetime import date, timedelta

from .domain import Bar


class MarketDataProvider:
    def bars(self, symbol: str) -> list[Bar]:
        raise NotImplementedError


class DemoMarketData(MarketDataProvider):
    """Deterministic offline data so the project works without API keys."""

    def __init__(self, days: int = 80) -> None:
        self.days = days

    def bars(self, symbol: str) -> list[Bar]:
        start = date(2026, 1, 5)
        price = 30.0
        out: list[Bar] = []
        produced = 0
        i = 0
        while produced < self.days:
            d = start + timedelta(days=i)
            i += 1
            if d.weekday() >= 5:
                continue

            prev = price
            drift = 0.002 if produced < 25 else (-0.003 if produced < 45 else 0.004)
            wave = ((produced % 7) - 3) * 0.001
            price = max(5.0, prev * (1 + drift + wave))
            close = round(price, 2)
            out.append(
                Bar(
                    symbol=symbol,
                    trading_date=d,
                    open=round((prev + close) / 2, 2),
                    high=round(max(prev, close) * 1.01, 2),
                    low=round(min(prev, close) * 0.99, 2),
                    close=close,
                    volume=1_000_000 + produced * 10_000,
                    prev_close=round(prev, 2),
                )
            )
            produced += 1
        return out
