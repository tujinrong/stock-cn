from __future__ import annotations

from .account import Account
from .domain import Bar, Fill, Order, Side
from .rules import AShareRules


class PaperBroker:
    def __init__(self, account: Account, rules: AShareRules | None = None) -> None:
        self.account = account
        self.rules = rules or AShareRules()

    def execute(self, order: Order, bar: Bar, price: float | None = None) -> Fill:
        self.rules.validate_quantity(order.side, order.quantity)
        fill_price = float(price if price is not None else bar.close)

        if not self.rules.can_trade_at(bar, order.side, fill_price):
            raise ValueError("order cannot be filled under current price-limit conditions")

        gross = fill_price * order.quantity
        fee = self.rules.fees(order.side, gross)

        if order.side is Side.BUY:
            if gross + fee > self.account.cash:
                raise ValueError("insufficient cash")
        else:
            pos = self.account.position(order.symbol)
            if order.quantity > pos.available:
                raise ValueError("insufficient T+1 sellable shares")

        fill = Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            fee=fee,
            trading_date=bar.trading_date,
        )
        self.account.apply_fill(fill)
        return fill
