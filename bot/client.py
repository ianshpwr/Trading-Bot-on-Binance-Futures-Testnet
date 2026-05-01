from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests
from requests import Response
from requests.exceptions import RequestException

from bot.logging_config import get_logger


BASE_URL = "https://demo-fapi.binance.com"



class BinanceAPIError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[APIError {code}] {message}")


class NetworkError(Exception):
    pass


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        signed_params = dict(params)
        signed_params["timestamp"] = int(time.time() * 1000)

        query_string = urlencode(signed_params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signed_params["signature"] = signature

        safe_params = {
            key: value
            for key, value in signed_params.items()
            if key != "signature"
        }
        self.logger.debug("Request params: %s", safe_params)
        return signed_params

    def post(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        signed_params = self._sign(params)
        url = f"{BASE_URL}{endpoint}"

        try:
            response = self.session.post(url, params=signed_params, timeout=10)
        except RequestException as exc:
            self.logger.error("Network failure while calling %s: %s", endpoint, exc)
            raise NetworkError("Could not reach Binance") from exc

        return self._handle_response(response)

    def _handle_response(self, response: Response) -> dict[str, Any]:
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"msg": response.text or "Unknown response from Binance"}

        self.logger.debug("Response status=%s body=%s", response.status_code, response_data)

        if response.status_code >= 400:
            error_code = int(response_data.get("code", response.status_code))
            error_message = str(response_data.get("msg", "Unknown Binance API error"))
            self.logger.error("API error %s: %s", error_code, error_message)
            raise BinanceAPIError(code=error_code, message=error_message)

        return response_data

