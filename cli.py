from __future__ import annotations

import os
import sys
from typing import Any

import typer
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.table import Table

from bot.client import BinanceAPIError, BinanceClient, NetworkError
from bot.logging_config import get_logger
from bot.orders import OrderManager, OrderResult
from bot.validators import validate_all


app = typer.Typer(help="CLI trading bot for Binance Futures Testnet (USDT-M).")
console = Console()
logger = get_logger(__name__)


def _load_credentials() -> tuple[str, str]:
    load_dotenv()

    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", "").strip()

    if not api_key:
        console.print(
            "❌ Error: BINANCE_TESTNET_API_KEY not found in environment. Check your .env file."
        )
        sys.exit(1)

    if not api_secret:
        console.print(
            "❌ Error: BINANCE_TESTNET_API_SECRET not found in environment. Check your .env file."
        )
        sys.exit(1)

    logger.info("Application startup complete, credentials loaded")
    return api_key, api_secret


def _build_summary_table(validated_inputs: dict[str, Any]) -> Table:
    table = Table(
        title="ORDER SUMMARY",
        box=box.ROUNDED,
        show_header=False,
        expand=False,
    )
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Symbol", str(validated_inputs["symbol"]))
    table.add_row("Side", str(validated_inputs["side"]))
    table.add_row("Type", str(validated_inputs["order_type"]))
    table.add_row("Quantity", f'{validated_inputs["quantity"]:.3f}')

    price = validated_inputs.get("price")
    stop_price = validated_inputs.get("stop_price")

    if price is not None:
        table.add_row("Price", f"{price:.2f}")

    if stop_price is not None:
        table.add_row("Stop Price", f"{stop_price:.2f}")

    return table


def _build_result_table(order_result: OrderResult) -> Table:
    table = Table(
        title="ORDER RESULT",
        box=box.ROUNDED,
        show_header=False,
        expand=False,
    )
    table.add_column("Field", style="bold green")
    table.add_column("Value", style="white")

    table.add_row("Order ID", str(order_result.order_id))
    table.add_row("Status", order_result.status)
    table.add_row("Executed Qty", f"{order_result.executed_qty:.3f}")
    table.add_row("Avg Price", f"{order_result.avg_price:.2f}")

    return table


def _print_validation_errors(error_message: str) -> None:
    for error in error_message.splitlines():
        console.print(f"❌ {error}")


@app.command("place-order")
def place_order(
    symbol: str = typer.Option(..., "--symbol", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", help="Order side: BUY or SELL"),
    order_type: str = typer.Option(
        ...,
        "--type",
        help="Order type: MARKET, LIMIT, or STOP",
    ),
    quantity: float = typer.Option(..., "--quantity", help="Amount to trade"),
    price: float | None = typer.Option(
        None,
        "--price",
        help="Limit price for LIMIT or STOP orders",
    ),
    stop_price: float | None = typer.Option(
        None,
        "--stop-price",
        help="Stop trigger price for STOP orders",
    ),
) -> None:
    api_key, api_secret = _load_credentials()

    try:
        validated_inputs = validate_all(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValueError as exc:
        _print_validation_errors(str(exc))
        raise typer.Exit(code=1) from exc

    console.print(_build_summary_table(validated_inputs))

    client = BinanceClient(api_key=api_key, api_secret=api_secret)
    order_manager = OrderManager(client=client)

    try:
        order_result = _dispatch_order(order_manager, validated_inputs)
        console.print(_build_result_table(order_result))
        console.print("✅ Order placed successfully!")
        raise typer.Exit(code=0)
    except BinanceAPIError as exc:
        logger.error("Binance API error while placing order: code=%s message=%s", exc.code, exc.message)
        console.print(f"❌ API Error [{exc.code}]: {exc.message}")
        raise typer.Exit(code=2) from exc
    except NetworkError as exc:
        logger.error("Network error while placing order: %s", exc)
        console.print("❌ Network error: could not reach Binance")
        raise typer.Exit(code=3) from exc
    except typer.Exit:
        raise
    except Exception as exc:
        logger.critical("Unhandled exception while placing order", exc_info=exc)
        console.print("❌ Unexpected error")
        raise typer.Exit(code=99) from exc


def _dispatch_order(
    order_manager: OrderManager,
    validated_inputs: dict[str, Any],
) -> OrderResult:
    order_type = str(validated_inputs["order_type"])

    if order_type == "MARKET":
        return order_manager.place_market_order(
            symbol=str(validated_inputs["symbol"]),
            side=str(validated_inputs["side"]),
            quantity=float(validated_inputs["quantity"]),
        )

    if order_type == "LIMIT":
        return order_manager.place_limit_order(
            symbol=str(validated_inputs["symbol"]),
            side=str(validated_inputs["side"]),
            quantity=float(validated_inputs["quantity"]),
            price=float(validated_inputs["price"]),
        )

    return order_manager.place_stop_limit_order(
        symbol=str(validated_inputs["symbol"]),
        side=str(validated_inputs["side"]),
        quantity=float(validated_inputs["quantity"]),
        price=float(validated_inputs["price"]),
        stop_price=float(validated_inputs["stop_price"]),
    )


if __name__ == "__main__":
    app()
