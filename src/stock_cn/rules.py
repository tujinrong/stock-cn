from __future__ import annotations

from dataclasses import dataclass

from .domain import Bar, Side


@dataclass(frozen=True)
class RuleConfig:
    commission_rate: float = 0.00025
    min_commission: float = 5.0
    stamp_duty_sell_rate: float = 0.0005
    transfer_fee_rate: float = 0.00001
    main_board_limit: float = 0.10
    growth_board_limit: float = 0.20
    st_limit: float = 0.05
    lot_size: int = 100


class AShareRules:
    """Engineering-level simplified A-share trading rules."""

    def __init__(self, config: RuleConfig | None = None) -> None:
        self.config = config or RuleConfig()

    def board_limit(self, symbol: str, is_st: bool = False) -> float:
        if is_st:
            return self.config.st_limit
        code = symbol.split(".")[0]
        if code.startswith(("300", "301", "688", "689")):
            return self.config.growth_board_limit
        return self.config.main_board_limit

    def price_limits(self, bar: Bar) -> tuple[float, float]:
        pct = self.board_limit(bar.symbol, bar.is_st)
        return round(bar.prev_close * (1 - pct), 2), round(bar.prev_close * (1 + pct), 2)

    def validate_quantity(self, side: Side, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if side is Side.BUY and quantity % self.config.lot_size != 0:
            raise ValueError(f"buy quantity must be a multiple of {self.config.lot_size}")

    def can_trade_at(self, bar: Bar, side: Side, price: float) -> bool:
        down, up = self.price_limits(bar)
        if side is Side.BUY and price >= up and bar.low >= up:
            return False
        if side is Side.SELL and price <= down and bar.high <= down:
            return False
        return down <= price <= up

    def fees(self, side: Side, gross_amount: float) -> float:
        commission = max(gross_amount * self.config.commission_rate, self.config.min_commission)
        transfer = gross_amount * self.config.transfer_fee_rate
        stamp = gross_amount * self.config.stamp_duty_sell_rate if side is Side.SELL else 0.0
        return commission + transfer + stamp
