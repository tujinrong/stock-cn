"""Shared paper-trading decision contract and single-order execution.

Both historical SIMULATION and live FORMAL Paper Trading must use this module.
Mode adapters may change evidence timing and execution quote provenance, but not
the decision schema, cash/T+1/lot/limit checks or accounting math.
"""
from __future__ import annotations

import copy
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from .sim_data import number


class PaperCoreError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise PaperCoreError(message)


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def money(value):
    return str(number(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def validate_decision_contract(response, request, symbol_validator, *, quote_validator=None):
    """Validate the mode-independent AI decision contract."""
    _require(isinstance(response, dict), "AI response must be an object")
    c = request["context"]
    _require(_integer(response.get("input_revision")), "input_revision must be integer")
    _require(response.get("schema_version") == "0.3-draft", "unsupported decision schema")
    _require(not ({"orders", "trades", "execute", "instructions"} & response.keys()),
             "unexpected execution payload")
    for name in ("strategy_id", "variant_id", "mode", "run_id", "decision_id",
                 "date", "decision_time", "input_revision", "input_commit"):
        _require(response.get(name) == c[name], f"AI identity/version/time mismatch: {name}")
    _require(response.get("status") == "READY",
             "AI did not complete decision: " + str(response.get("status")))
    _require(isinstance(response.get("summary"), str) and response["summary"].strip(),
             "missing summary")
    for name in ("evidence", "risks", "data_gaps"):
        _require(isinstance(response.get(name), list), f"missing list: {name}")
    cutoff = datetime.fromisoformat(c["information_cutoff"])
    for item in response["evidence"]:
        _require(item.get("source") and item.get("published_at"), "evidence provenance missing")
        dt = datetime.fromisoformat(item["published_at"])
        _require(dt.tzinfo is not None and dt <= cutoff, "future evidence")
    action = response.get("action")
    _require(action in {"BUY", "SELL", "HOLD"}, "unknown action")
    order = response.get("order_proposal")
    if action == "HOLD":
        _require(order is None, "HOLD must not carry orders")
    else:
        _require(isinstance(order, dict) and order.get("side") == action,
                 "only one order with matching side")
        _require(_integer(order.get("quantity")) and order["quantity"] > 0,
                 "quantity must be a positive integer")
        symbol_validator(order.get("symbol"))
        _require(number(order.get("reference_price_cny")) > 0, "missing reference price")
        t = datetime.fromisoformat(order["quote_time"])
        _require(t.tzinfo and t <= cutoff, "future reference quote")
        _require(order.get("quote_source"), "quote provenance missing")
        if quote_validator:
            quote_validator(order, request)
    weights, cash = response.get("target_weights"), response.get("target_cash_weight")
    _require((weights is None) == (cash is None), "incomplete target weights")
    if weights is not None:
        _require(isinstance(weights, dict), "target_weights must be symbol/weight object")
        for symbol, weight in weights.items():
            symbol_validator(symbol)
            _require(0 <= number(weight) <= 1, "invalid target weight")
        _require(0 <= number(cash) <= 1 and
                 abs(sum(number(v) for v in weights.values()) + number(cash) - 1)
                 < Decimal("0.000001"), "weights do not sum to one")
    return True


def execute_single_order(state, response, quote, instrument, fees, *,
                         mode, execution_basis, execution_time):
    """Apply exactly zero or one Paper Trading order to a copied account state.

    quote keys: price, source, quote_time, suspended, limit_up, limit_down.
    This function deliberately knows nothing about historical vs live data.
    """
    _require(mode in {"SIMULATION", "FORMAL"}, "unsupported paper mode")
    after = copy.deepcopy(state)
    execution = {
        "status": "NO_TRADE", "fill": None, "reason": "HOLD",
        "decision_id": response["decision_id"], "paper_only": True,
        "mode": mode, "execution_basis": execution_basis,
    }
    order = response.get("order_proposal")
    if not order:
        return after, execution

    symbol, side, quantity = order["symbol"], order["side"], order["quantity"]
    price = number(quote["price"])
    gross = price * quantity
    commission = max(number(fees["min_commission"]),
                     gross * number(fees["commission_rate"]))
    fee = number(money(
        commission + gross * number(fees["transfer_fee_rate"]) +
        (gross * number(fees["stamp_duty_sell_rate"]) if side == "SELL" else 0)
    ))
    p = next((x for x in after["positions"] if x["symbol"] == symbol), None)
    lot_size = int(instrument.get("lot_size", 100))
    reason = None
    if quote.get("suspended"):
        reason = "SUSPENDED"
    elif side == "BUY" and quantity % lot_size:
        reason = "BOARD_LOT"
    elif side == "SELL" and (p is None or quantity > p["sellable_quantity"]):
        reason = "INSUFFICIENT_T1_SHARES"
    elif side == "SELL" and quantity % lot_size and quantity != p["sellable_quantity"]:
        reason = "ODD_LOT_MUST_CLEAR_REMAINDER"
    elif side == "BUY" and gross + fee > number(after["cash_cny"]):
        reason = "INSUFFICIENT_CASH_AT_EXECUTION_PRICE"
    elif quote.get("limit_up") is None or quote.get("limit_down") is None:
        reason = "MISSING_DAILY_LIMIT_METADATA"
    elif side == "BUY" and price >= number(quote["limit_up"]):
        reason = "LIMIT_UP_CONSERVATIVE_NO_FILL"
    elif side == "SELL" and price <= number(quote["limit_down"]):
        reason = "LIMIT_DOWN_CONSERVATIVE_NO_FILL"

    if reason:
        execution.update(status="REJECTED", reason=reason)
        return after, execution

    if side == "BUY":
        if p is None:
            p = {
                "symbol": symbol, "name": instrument["name"], "quantity": 0,
                "sellable_quantity": 0, "average_cost_cny": "0.00",
                "cost_basis_cny": "0.00", "valuation_price_cny": money(price),
            }
            after["positions"].append(p)
        total_cost = number(p["cost_basis_cny"]) + gross + fee
        p["quantity"] += quantity
        p["cost_basis_cny"] = money(total_cost)
        p["average_cost_cny"] = str(
            (total_cost / p["quantity"]).quantize(Decimal("0.000001"),
                                                   rounding=ROUND_HALF_UP)
        )
        after["cash_cny"] = money(number(after["cash_cny"]) - gross - fee)
    else:
        p["cost_basis_cny"] = money(
            number(p["cost_basis_cny"]) * (p["quantity"] - quantity) / p["quantity"]
        )
        p["quantity"] -= quantity
        p["sellable_quantity"] -= quantity
        after["cash_cny"] = money(number(after["cash_cny"]) + gross - fee)
        if p["quantity"] == 0:
            after["positions"].remove(p)

    after["_meta"]["fees_cny"] = money(number(after["_meta"].get("fees_cny", 0)) + fee)
    execution.update(
        status="FILLED",
        reason="PAPER_FILL_USING_MODE_QUOTE",
        fill={
            "symbol": symbol, "side": side, "quantity": quantity,
            "price_cny": money(price), "fee_cny": money(fee),
            "time": execution_time, "source": quote["source"],
            "quote_time": quote["quote_time"], "time_basis": execution_basis,
        },
    )
    return after, execution
