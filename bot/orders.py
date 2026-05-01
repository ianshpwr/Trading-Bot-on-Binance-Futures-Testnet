from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bot.client import BinanceClient
from bot.logging_config import get_logger


@dataclass
class OrderResult:
    order_id: int
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: float
    executed_qty: float
    avg_price: float
    raw_response: dict[str, Any]


class OrderManager:
    def __init__(self, client: BinanceClient) -> None:
        self.client = client
        self.logger = get_logger(__name__)

    def place_market_order(self, symbol: str, side: str, quantity: float) -> OrderResult:
        self.logger.info(
            "Placing MARKET %s order — %s qty=%s",
            side,
            symbol,
            quantity,
        )
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": self._format_decimal(quantity),
            "newOrderRespType": "RESULT",
        }
        response = self.client.post("/fapi/v1/order", params)
        self.logger.debug("Raw MARKET order response: %s", response)
        self.logger.info("Order success: orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return self._to_order_result(response)

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        self.logger.info(
            "Placing LIMIT %s order — %s qty=%s",
            side,
            symbol,
            quantity,
        )
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": self._format_decimal(quantity),
            "price": self._format_decimal(price),
            "timeInForce": time_in_force,
        }
        response = self.client.post("/fapi/v1/order", params)
        self.logger.debug("Raw LIMIT order response: %s", response)
        self.logger.info("Order success: orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return self._to_order_result(response)

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        self.logger.info(
            "Placing STOP %s order — %s qty=%s",
            side,
            symbol,
            quantity,
        )
        params = {
            "algoType": "CONDITIONAL",
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "quantity": self._format_decimal(quantity),
            "price": self._format_decimal(price),
            "triggerPrice": self._format_decimal(stop_price),
            "timeInForce": time_in_force,
            "newOrderRespType": "RESULT",
        }
        response = self.client.post("/fapi/v1/algoOrder", params)
        self.logger.debug("Raw STOP order response: %s", response)
        self.logger.info(
            "Order success: orderId=%s status=%s",
            response.get("algoId"),
            response.get("algoStatus"),
        )
        return self._to_order_result(response)

    def _to_order_result(self, response: dict[str, Any]) -> OrderResult:
        if "algoId" in response:
            return OrderResult(
                order_id=int(response["algoId"]),
                symbol=str(response["symbol"]),
                side=str(response["side"]),
                order_type=str(response["orderType"]),
                status=str(response["algoStatus"]),
                quantity=float(response["quantity"]),
                executed_qty=0.0,
                avg_price=float(response.get("price", 0) or 0),
                raw_response=response,
            )

        return OrderResult(
            order_id=int(response["orderId"]),
            symbol=str(response["symbol"]),
            side=str(response["side"]),
            order_type=str(response["type"]),
            status=str(response["status"]),
            quantity=float(response["origQty"]),
            executed_qty=float(response["executedQty"]),
            avg_price=float(response.get("avgPrice", 0)),
            raw_response=response,
        )

    def _format_decimal(self, value: float) -> str:
        return f"{value:.8f}".rstrip("0").rstrip(".")
