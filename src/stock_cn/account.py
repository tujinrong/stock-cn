from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .domain import Fill, Position, Side


@dataclass
class Account:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    fills: list[Fill] = field(default_factory=list)
    _bought_today: dict[tuple[date, str], int] = field(default_factory=dict)

    def position(self, symbol: str) -> Position:
        return self.positions.setdefault(symbol, Position(symbol=symbol))

    def mark(self, symbol: str, price: float) -> None:
        self.position(symbol).last_price = price

    def begin_day(self, trading_date: date) -> None:
        for pos in self.positions.values():
            pos.available = pos.quantity
        self._bought_today = {
            key: qty for key, qty in self._bought_today.items() if key[0] == trading_date
        }

    def apply_fill(self, fill: Fill) -> None:
        pos = self.position(fill.symbol)
        gross = fill.price * fill.quantity

        if fill.side is Side.BUY:
            total_cost_before = pos.average_cost * pos.quantity
            total_cost_after = total_cost_before + gross + fill.fee
            pos.quantity += fill.quantity
            pos.average_cost = total_cost_after / pos.quantity
            self.cash -= gross + fill.fee
            self._bought_today[(fill.trading_date, fill.symbol)] = (
                self._bought_today.get((fill.trading_date, fill.symbol), 0) + fill.quantity
            )
        else:
            if fill.quantity > pos.available:
                raise ValueError("T+1 violation or insufficient sellable quantity")
            pos.quantity -= fill.quantity
            pos.available -= fill.quantity
            self.cash += gross - fill.fee
            if pos.quantity == 0:
                pos.average_cost = 0.0

        pos.last_price = fill.price
        self.fills.append(fill)

    @property
    def market_value(self) -> float:
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_equity(self) -> float:
        return self.cash + self.market_value
