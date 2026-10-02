from datetime import date

import pytest

from stock_cn.account import Account
from stock_cn.broker import PaperBroker
from stock_cn.domain import Bar, Order, Side


def bar(day: int, close: float = 10.0) -> Bar:
    return Bar(
        symbol="600036.SH",
        trading_date=date(2026, 1, day),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1_000_000,
        prev_close=close,
    )


def test_buy_must_be_board_lot() -> None:
    broker = PaperBroker(Account(100_000))
    with pytest.raises(ValueError):
        broker.execute(Order("600036.SH", Side.BUY, 50), bar(5))


def test_t_plus_one_blocks_same_day_sell() -> None:
    account = Account(100_000)
    broker = PaperBroker(account)
    d1 = bar(5)

    account.begin_day(d1.trading_date)
    broker.execute(Order("600036.SH", Side.BUY, 100), d1)

    with pytest.raises(ValueError):
        broker.execute(Order("600036.SH", Side.SELL, 100), d1)


def test_t_plus_one_allows_next_day_sell() -> None:
    account = Account(100_000)
    broker = PaperBroker(account)
    d1 = bar(5)
    d2 = bar(6, 10.2)

    account.begin_day(d1.trading_date)
    broker.execute(Order("600036.SH", Side.BUY, 100), d1)

    account.begin_day(d2.trading_date)
    fill = broker.execute(Order("600036.SH", Side.SELL, 100), d2)

    assert fill.quantity == 100
    assert account.position("600036.SH").quantity == 0
