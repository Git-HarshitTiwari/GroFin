"""
Order service for GroFin.

This module coordinates validation and Binance client calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from grofin.bot.client import BinanceFuturesClient
from grofin.bot.logging_config import get_logger
from grofin.bot.validators import validate_order_inputs


logger = get_logger("orders")


@dataclass(frozen=True)
class OrderRequest:
    """A validated GroFin order request."""

    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None


@dataclass(frozen=True)
class OrderResult:
    """A clean result object for CLI rendering."""

    request: OrderRequest
    response: dict[str, Any]


class OrderService:
    """
    High-level order workflow used by the GroFin CLI.
    """

    def __init__(self, client: BinanceFuturesClient | None = None) -> None:
        self.client = client or BinanceFuturesClient()

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: str | None = None,
    ) -> OrderResult:
        """Validate input, place the order, and return a render-ready result."""

        validated_input = validate_order_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )

        order_request = OrderRequest(
            symbol=str(validated_input["symbol"]),
            side=str(validated_input["side"]),
            order_type=str(validated_input["order_type"]),
            quantity=validated_input["quantity"],  # type: ignore[arg-type]
            price=validated_input["price"],  # type: ignore[arg-type]
        )

        logger.info("GroFin validated order request: %s", order_request)

        response = self.client.place_order(
            symbol=order_request.symbol,
            side=order_request.side,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=order_request.price,
        )

        logger.info(
            "GroFin order placed successfully: order_id=%s status=%s",
            response.get("orderId"),
            response.get("status"),
        )

        return OrderResult(request=order_request, response=response)
