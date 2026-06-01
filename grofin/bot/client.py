"""
Binance Futures Testnet API client for GroFin.

This module contains the low-level HTTP logic only:
loading credentials, signing requests, sending API calls, and handling failures.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from requests import Response
from requests.exceptions import RequestException, Timeout

from grofin.bot.logging_config import get_logger


BINANCE_FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT_SECONDS = 10

logger = get_logger("client")


class GroFinClientError(Exception):
    """Base exception for GroFin Binance client failures."""


class MissingCredentialsError(GroFinClientError):
    """Raised when Binance API credentials are not available."""


class BinanceAPIError(GroFinClientError):
    """Raised when Binance returns an error response."""


class BinanceNetworkError(GroFinClientError):
    """Raised when GroFin cannot reach Binance reliably."""


class BinanceFuturesClient:
    """
    Minimal Binance USDT-M Futures Testnet REST client for GroFin.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str = BINANCE_FUTURES_TESTNET_URL,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        load_dotenv()

        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        if not self.api_key or not self.api_secret:
            raise MissingCredentialsError(
                "Missing Binance credentials. Add BINANCE_API_KEY and "
                "BINANCE_API_SECRET to your .env file."
            )

        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        logger.debug("GroFin Binance Futures Testnet client initialized.")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Decimal | None = None,
    ) -> dict[str, Any]:
        """
        Place a MARKET or LIMIT order on Binance Futures Testnet.
        """

        payload: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": self._decimal_to_string(quantity),
            "timestamp": self._timestamp_ms(),
        }

        if order_type == "LIMIT":
            payload["price"] = self._decimal_to_string(price)
            payload["timeInForce"] = "GTC"

        logger.info(
            "GroFin sending order request: symbol=%s side=%s type=%s quantity=%s price=%s",
            symbol,
            side,
            order_type,
            quantity,
            price,
        )

        return self._signed_request("POST", "/fapi/v1/order", payload)

    def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Send an authenticated signed request to Binance.
        """

        params["signature"] = self._signature(params)
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout,
            )
        except Timeout as exc:
            logger.exception("GroFin Binance request timed out.")
            raise BinanceNetworkError("Binance request timed out. Try again.") from exc
        except RequestException as exc:
            logger.exception("GroFin Binance network request failed.")
            raise BinanceNetworkError(
                "Network error while contacting Binance Futures Testnet."
            ) from exc

        return self._handle_response(response)

    def _handle_response(self, response: Response) -> dict[str, Any]:
        """
        Convert a Binance HTTP response into a Python dictionary.
        """

        logger.info(
            "GroFin received Binance response: status_code=%s body=%s",
            response.status_code,
            response.text,
        )

        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("GroFin received non-JSON response from Binance.")
            raise BinanceAPIError("Binance returned an unreadable response.") from exc

        if response.status_code >= 400:
            message = data.get("msg", "Binance API request failed.")
            code = data.get("code", response.status_code)
            logger.error("GroFin Binance API error: code=%s message=%s", code, message)
            raise BinanceAPIError(f"Binance API error {code}: {message}")

        return data

    def _signature(self, params: dict[str, Any]) -> str:
        """
        Create the HMAC SHA256 signature required by Binance.
        """

        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _timestamp_ms() -> int:
        """
        Return the current Unix timestamp in milliseconds.
        """

        return int(time.time() * 1000)

    @staticmethod
    def _decimal_to_string(value: Decimal | None) -> str:
        """
        Convert Decimal values to Binance-friendly strings.
        """

        if value is None:
            raise ValueError("Decimal value cannot be None.")
        return format(value.normalize(), "f")
