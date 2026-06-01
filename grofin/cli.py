"""
Command-line interface for GroFin.
"""

from __future__ import annotations

import logging
from typing import Optional

import typer
from rich.console import Console
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from grofin.bot.client import (
    BinanceAPIError,
    BinanceNetworkError,
    MissingCredentialsError,
)
from grofin.bot.logging_config import setup_logging
from grofin.bot.orders import OrderResult, OrderService
from grofin.bot.validators import ValidationError


app = typer.Typer(
    name="GroFin",
    help="GroFin places Binance Futures Testnet orders from a clean Python CLI.",
    add_completion=False,
)
console = Console()


def _print_banner() -> None:
    """Show the GroFin brand mark before CLI output."""

    banner = Text()
    banner.append("  ____            _____ _       \n", style="bold cyan")
    banner.append(" / ___|_ __ ___  |  ___(_)_ __  \n", style="bold cyan")
    banner.append("| |  _| '__/ _ \\ | |_  | | '_ \\ \n", style="bold cyan")
    banner.append("| |_| | | | (_) ||  _| | | | | |\n", style="bold cyan")
    banner.append(" \\____|_|  \\___/ |_|   |_|_| |_|\n", style="bold cyan")
    banner.append("\nBinance Futures Testnet Trading Bot", style="white")

    console.print(Align.center(banner))


def _render_order_summary(result: OrderResult) -> None:
    """Render the order request that GroFin sent to Binance."""

    request = result.request
    table = Table(title="Order Request Summary", border_style="cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Symbol", request.symbol)
    table.add_row("Side", request.side)
    table.add_row("Type", request.order_type)
    table.add_row("Quantity", str(request.quantity))
    table.add_row("Price", str(request.price) if request.price else "N/A")

    console.print(table)


def _render_order_response(result: OrderResult) -> None:
    """Render the important Binance response fields."""

    response = result.response
    table = Table(title="Binance Response Details", border_style="green")
    table.add_column("Field", style="bold")
    table.add_column("Value", style="white")

    table.add_row("Order ID", str(response.get("orderId", "N/A")))
    table.add_row("Status", str(response.get("status", "N/A")))
    table.add_row("Executed Qty", str(response.get("executedQty", "N/A")))
    table.add_row("Average Price", str(response.get("avgPrice", "N/A")))
    table.add_row("Symbol", str(response.get("symbol", "N/A")))
    table.add_row("Side", str(response.get("side", "N/A")))
    table.add_row("Type", str(response.get("type", "N/A")))

    console.print(table)


def _exit_with_error(message: str) -> None:
    """Print a user-friendly error and exit with a failing status code."""

    console.print(Panel(f"[bold red]{message}[/bold red]", title="GroFin Error"))
    raise typer.Exit(code=1)


@app.command()
def order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, for example BTCUSDT."),
    side: str = typer.Option(..., "--side", help="BUY or SELL."),
    order_type: str = typer.Option(
        ...,
        "--type",
        "-t",
        help="Order type: MARKET or LIMIT.",
    ),
    quantity: str = typer.Option(..., "--quantity", "-q", help="Order quantity."),
    price: Optional[str] = typer.Option(
        None,
        "--price",
        "-p",
        help="Limit price. Required only for LIMIT orders.",
    ),
) -> None:
    """Place a MARKET or LIMIT order on Binance Futures Testnet."""

    setup_logging(logging.INFO)
    _print_banner()

    try:
        service = OrderService()
        result = service.create_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except ValidationError as exc:
        _exit_with_error(str(exc))
    except MissingCredentialsError as exc:
        _exit_with_error(str(exc))
    except BinanceNetworkError as exc:
        _exit_with_error(str(exc))
    except BinanceAPIError as exc:
        _exit_with_error(str(exc))
    except Exception as exc:
        logging.getLogger("GroFin.cli").exception("Unexpected GroFin CLI failure.")
        _exit_with_error(f"Unexpected error: {exc}")

    _render_order_summary(result)
    _render_order_response(result)
    console.print("[bold green]GroFin order request completed successfully.[/bold green]")


@app.command()
def interactive() -> None:
    """Place an order using guided GroFin prompts."""

    setup_logging(logging.INFO)
    _print_banner()

    symbol = typer.prompt("Symbol", default="BTCUSDT")
    side = typer.prompt("Side", default="BUY")
    order_type = typer.prompt("Order type", default="MARKET")
    quantity = typer.prompt("Quantity")
    price: str | None = None

    if order_type.strip().upper() == "LIMIT":
        price = typer.prompt("Limit price")

    try:
        service = OrderService()
        result = service.create_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
    except ValidationError as exc:
        _exit_with_error(str(exc))
    except MissingCredentialsError as exc:
        _exit_with_error(str(exc))
    except BinanceNetworkError as exc:
        _exit_with_error(str(exc))
    except BinanceAPIError as exc:
        _exit_with_error(str(exc))
    except Exception as exc:
        logging.getLogger("GroFin.cli").exception("Unexpected GroFin CLI failure.")
        _exit_with_error(f"Unexpected error: {exc}")

    _render_order_summary(result)
    _render_order_response(result)
    console.print("[bold green]GroFin order request completed successfully.[/bold green]")


if __name__ == "__main__":
    app()
