from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from bot.logging_config import get_logger


logger = get_logger(__name__)


def validate_symbol(symbol: str) -> str:
    cleaned_symbol = symbol.strip().upper()

    if not cleaned_symbol:
        raise ValueError("Symbol must be a non-empty string")

    if not cleaned_symbol.endswith("USDT"):
        logger.warning("Symbol does not end with USDT: %s", cleaned_symbol)

    return cleaned_symbol


def validate_side(side: str) -> str:
    cleaned_side = side.strip().upper()

    if cleaned_side not in {"BUY", "SELL"}:
        raise ValueError("Side must be BUY or SELL")

    return cleaned_side


def validate_order_type(order_type: str) -> str:
    cleaned_order_type = order_type.strip().upper()

    if cleaned_order_type not in {"MARKET", "LIMIT", "STOP"}:
        raise ValueError("Order type must be MARKET, LIMIT, or STOP")

    return cleaned_order_type


def validate_quantity(quantity: float) -> float:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0")

    if _decimal_places(quantity) > 3:
        raise ValueError("Quantity must have no more than 3 decimal places")

    return float(quantity)


def validate_price(price: float | None, order_type: str) -> float | None:
    normalized_order_type = order_type.strip().upper()

    if normalized_order_type in {"LIMIT", "STOP"}:
        if price is None:
            raise ValueError(f"Price is required for {normalized_order_type} orders")
        if price <= 0:
            raise ValueError("Price must be greater than 0")
        return float(price)

    if normalized_order_type == "MARKET" and price is not None:
        logger.warning("Price provided for MARKET order will be ignored")

    return None


def validate_stop_price(stop_price: float | None, order_type: str) -> float | None:
    normalized_order_type = order_type.strip().upper()

    if normalized_order_type == "STOP":
        if stop_price is None:
            raise ValueError("Stop price is required for STOP orders")
        if stop_price <= 0:
            raise ValueError("Stop price must be greater than 0")
        return float(stop_price)

    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
    stop_price: float | None,
) -> dict[str, Any]:
    errors: list[str] = []
    validated: dict[str, Any] = {}

    try:
        validated["symbol"] = validate_symbol(symbol)
    except ValueError as exc:
        errors.append(str(exc))

    try:
        validated["side"] = validate_side(side)
    except ValueError as exc:
        errors.append(str(exc))

    try:
        validated["order_type"] = validate_order_type(order_type)
    except ValueError as exc:
        errors.append(str(exc))

    try:
        validated["quantity"] = validate_quantity(quantity)
    except ValueError as exc:
        errors.append(str(exc))

    if "order_type" in validated:
        try:
            validated["price"] = validate_price(price, validated["order_type"])
        except ValueError as exc:
            errors.append(str(exc))

        try:
            validated["stop_price"] = validate_stop_price(
                stop_price,
                validated["order_type"],
            )
        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        logger.warning("Validation failed: %s", "; ".join(errors))
        raise ValueError("\n".join(errors))

    logger.info("Validation passed")
    return validated


def _decimal_places(value: float) -> int:
    try:
        normalized = Decimal(str(value)).normalize()
    except InvalidOperation as exc:
        raise ValueError("Quantity must be a valid number") from exc

    exponent = normalized.as_tuple().exponent
    return abs(exponent) if exponent < 0 else 0

