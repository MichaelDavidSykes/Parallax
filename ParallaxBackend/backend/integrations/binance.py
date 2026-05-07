from __future__ import annotations

import json
import hmac
import time
from hashlib import sha256
from typing import Any, Dict, List
from urllib.parse import urlencode

import httpx


class BinanceClient:
    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        api_secret: str = "",
        timeout: float = 12,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    async def health(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/v3/ping")
        return {"status_code": response.status_code, "ok": response.is_success}

    async def ticker_prices(self, symbols: List[str]) -> List[Dict[str, Any]]:
        cleaned_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if not cleaned_symbols:
                response = await client.get(f"{self.base_url}/api/v3/ticker/price")
            elif len(cleaned_symbols) == 1:
                response = await client.get(
                    f"{self.base_url}/api/v3/ticker/price",
                    params={"symbol": cleaned_symbols[0]},
                )
            else:
                response = await client.get(
                    f"{self.base_url}/api/v3/ticker/price",
                    params={"symbols": json.dumps(cleaned_symbols, separators=(",", ":"))},
                )
            response.raise_for_status()
            payload = response.json()

        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            return []
        return [self._normalize_ticker(item) for item in payload if isinstance(item, dict)]

    def _normalize_ticker(self, item: Dict[str, Any]) -> Dict[str, Any]:
        price = item.get("price")
        try:
            numeric_price = float(price)
        except (TypeError, ValueError):
            numeric_price = 0
        return {
            "symbol": str(item.get("symbol") or ""),
            "price": numeric_price,
            "source": "binance-spot",
        }

    async def account(self) -> Dict[str, Any]:
        return await self._signed_get(
            "/api/v3/account",
            {"omitZeroBalances": "true", "recvWindow": "5000"},
        )

    async def account_snapshot(self, quote_asset: str = "USDT") -> Dict[str, Any]:
        payload = await self.account()
        balances = payload.get("balances", [])
        if not isinstance(balances, list):
            balances = []

        nonzero_balances = [
            self._normalize_balance(item)
            for item in balances
            if isinstance(item, dict) and self._balance_amount(item) > 0
        ]
        prices: Dict[str, float] = {}
        for item in nonzero_balances:
            asset = item["asset"]
            if asset in {quote_asset, "USD", "USDC", "BUSD"}:
                continue
            try:
                tickers = await self.ticker_prices([f"{asset}{quote_asset}"])
            except httpx.HTTPStatusError:
                continue
            if tickers:
                prices[asset] = float(tickers[0].get("price") or 0)

        total_value = 0.0
        holdings = []
        for item in nonzero_balances:
            asset = item["asset"]
            amount = item["total"]
            price = 1.0 if asset in {quote_asset, "USD", "USDC", "BUSD"} else float(prices.get(asset, 0))
            value = amount * price
            total_value += value
            holdings.append(
                {
                    "symbol": asset,
                    "quantity": amount,
                    "price": price,
                    "value": value,
                    "platform": "Binance",
                    "asset_type": "crypto",
                }
            )
        return {
            "platform": "Binance",
            "currency": quote_asset,
            "total_value": total_value,
            "holdings": holdings,
            "raw": {"accountType": payload.get("accountType")},
        }

    async def _signed_get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Binance API key and secret are not configured.")
        query_params = {**params, "timestamp": int(time.time() * 1000)}
        query = urlencode(query_params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            sha256,
        ).hexdigest()
        url = f"{self.base_url}{path}?{query}&signature={signature}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers={"X-MBX-APIKEY": self.api_key})
            response.raise_for_status()
            payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def _normalize_balance(self, item: Dict[str, Any]) -> Dict[str, Any]:
        free = self._float(item.get("free"))
        locked = self._float(item.get("locked"))
        return {
            "asset": str(item.get("asset") or ""),
            "free": free,
            "locked": locked,
            "total": free + locked,
        }

    def _balance_amount(self, item: Dict[str, Any]) -> float:
        return self._float(item.get("free")) + self._float(item.get("locked"))

    def _float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
