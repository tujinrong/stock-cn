from __future__ import annotations

from dataclasses import dataclass

from .domain import Bar, Order, Side


class Strategy:
    def on_bar(self, history: list[Bar], position_qty: int) -> list[Order]:
        raise NotImplementedError


@dataclass
class MovingAverageCrossStrategy(Strategy):
    symbol: str
    short_window: int = 5
    long_window: int = 20
    trade_quantity: int = 100

    def on_bar(self, history: list[Bar], position_qty: int) -> list[Order]:
        if len(history) < self.long_window + 1:
            return []

        closes = [b.close for b in history]
        prev_short = sum(closes[-self.short_window - 1:-1]) / self.short_window
        prev_long = sum(closes[-self.long_window - 1:-1]) / self.long_window
        now_short = sum(closes[-self.short_window:]) / self.short_window
        now_long = sum(closes[-self.long_window:]) / self.long_window

        if prev_short <= prev_long and now_short > now_long and position_qty == 0:
            return [Order(self.symbol, Side.BUY, self.trade_quantity)]

        if prev_short >= prev_long and now_short < now_long and position_qty > 0:
            return [Order(self.symbol, Side.SELL, position_qty)]

        return []
