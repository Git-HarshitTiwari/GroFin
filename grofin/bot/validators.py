"""
Input validation helpers for GroFin.

The CLI layer uses these functions before an order reaches the Binance client.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(ValueError):
    """Raised when GroFin receives invalid order input."""


def normalize_symbol(symbol: str) -> str:
    """Return a clean Binance symbol such as BTCUSDT."""

    cleaned_symbol = symbol.strip().upper()

    if not SYMBOL_PATTERN.fullmatch(cleaned_symbol):
        raise ValidationError(
            "Symbol must look like BTCUSDT: uppercase letters/numbers, 5-20 characters."
        )

    if not cleaned_symbol.endswith("USDT"):
        raise ValidationError("GroFin supports Binance USDT-M symbols only, like BTCUSDT.")

    return cleaned_symbol


def normalize_side(side: str) -> str:
    """Return BUY or SELL after validating the trade side."""

    cleaned_side = side.strip().upper()

    if cleaned_side not in VALID_SIDES:
        raise ValidationError("Side must be BUY or SELL.")

    return cleaned_side


def normalize_order_type(order_type: str) -> str:
    """Return MARKET or LIMIT after validating the order type."""

    cleaned_order_type = order_type.strip().upper()

    if cleaned_order_type not in VALID_ORDER_TYPES:
        raise ValidationError("Order type must be MARKET or LIMIT.")

    return cleaned_order_type


def parse_positive_decimal(value: str, field_name: str) -> Decimal:
    """Parse a positive decimal value from CLI text."""

    try:
        parsed_value = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValidationError(f"{field_name} must be a valid number.") from exc

    if parsed_value <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")

    return parsed_value


def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None,
) -> dict[str, str | Decimal | None]:
    """Validate and normalize a complete GroFin order request."""

    normalized_symbol = normalize_symbol(symbol)
    normalized_side = normalize_side(side)
    normalized_order_type = normalize_order_type(order_type)
    parsed_quantity = parse_positive_decimal(quantity, "Quantity")

    parsed_price: Decimal | None = None
    if normalized_order_type == "LIMIT":
        if price is None or not price.strip():
            raise ValidationError("Price is required for LIMIT orders.")
        parsed_price = parse_positive_decimal(price, "Price")

    if normalized_order_type == "MARKET" and price:
        raise ValidationError("Price should not be provided for MARKET orders.")

    return {
        "symbol": normalized_symbol,
        "side": normalized_side,
        "order_type": normalized_order_type,
        "quantity": parsed_quantity,
        "price": parsed_price,
    }
