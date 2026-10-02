from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Bar:
    symbol: str
    trading_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    prev_close: float
    is_st: bool = False


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int


@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    quantity: int
    price: float
    fee: float
    trading_date: date


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    available: int = 0
    average_cost: float = 0.0
    last_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.last_price

    @property
    def unrealized_pnl(self) -> float:
        if self.quantity <= 0:
            return 0.0
        return self.quantity * (self.last_price - self.average_cost)
