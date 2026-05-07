from __future__ import annotations

from typing import Any, Dict, List

import httpx


class Trading212NotConfigured(RuntimeError):
    pass


class Trading212Client:
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
        if not self.configured:
            return {"status_code": None, "ok": False, "status": "not configured"}
        try:
            response = await self._get("/equity/account/summary")
        except Exception:
            return {"status_code": None, "ok": False, "status": "unreachable"}
        if response.status_code in {401, 403}:
            return {"status_code": response.status_code, "ok": False, "status": "unauthorized"}
        return {
            "status_code": response.status_code,
            "ok": response.is_success,
            "status": "online" if response.is_success else "degraded",
        }

    async def account_info(self) -> Dict[str, Any]:
        return await self._get_json("/equity/account/info")

    async def account_summary(self) -> Dict[str, Any]:
        return await self._get_json("/equity/account/summary")

    async def account_cash(self) -> Dict[str, Any]:
        return await self._get_json("/equity/account/cash")

    async def portfolio(self) -> List[Dict[str, Any]]:
        try:
            payload = await self._get_json("/equity/positions")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise
            payload = await self._get_json("/equity/portfolio")
        return payload if isinstance(payload, list) else []

    async def pending_orders(self) -> List[Dict[str, Any]]:
        payload = await self._get_json("/equity/orders")
        return payload if isinstance(payload, list) else []

    async def historical_orders(
        self,
        ticker: str = "",
        limit: int = 50,
        max_pages: int = 4,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": min(max(limit, 1), 50)}
        if ticker:
            params["ticker"] = ticker
        return await self._paginate("/equity/history/orders", params, max_pages=max_pages)

    async def market_order(
        self,
        ticker: str,
        quantity: float,
        extended_hours: bool = False,
    ) -> Dict[str, Any]:
        payload = await self._post_json(
            "/equity/orders/market",
            {
                "ticker": ticker,
                "quantity": quantity,
                "extendedHours": extended_hours,
            },
        )
        return payload if isinstance(payload, dict) else {}

    async def account_snapshot(self) -> Dict[str, Any]:
        return {
            "summary": await self.account_summary(),
            "info": await self.account_info(),
            "cash": await self.account_cash(),
            "positions": await self.portfolio(),
            "pending_orders": await self.pending_orders(),
            "historical_orders": await self.historical_orders(limit=50, max_pages=2),
            "source": "trading212",
        }

    async def _get(self, path: str) -> httpx.Response:
        if not self.configured:
            raise Trading212NotConfigured("Trading 212 API key and secret are not configured.")
        async with httpx.AsyncClient(
            timeout=self.timeout,
            auth=httpx.BasicAuth(self.api_key, self.api_secret),
        ) as client:
            return await client.get(f"{self.base_url}{path}")

    async def _post(self, path: str, payload: Dict[str, Any]) -> httpx.Response:
        if not self.configured:
            raise Trading212NotConfigured("Trading 212 API key and secret are not configured.")
        async with httpx.AsyncClient(
            timeout=self.timeout,
            auth=httpx.BasicAuth(self.api_key, self.api_secret),
        ) as client:
            return await client.post(f"{self.base_url}{path}", json=payload)

    async def _get_json(self, path: str, params: Dict[str, Any] | None = None) -> Any:
        response = await self._get_with_params(path, params or {})
        response.raise_for_status()
        return response.json()

    async def _post_json(self, path: str, payload: Dict[str, Any]) -> Any:
        response = await self._post(path, payload)
        response.raise_for_status()
        return response.json()

    async def _get_with_params(self, path: str, params: Dict[str, Any]) -> httpx.Response:
        if not self.configured:
            raise Trading212NotConfigured("Trading 212 API key and secret are not configured.")
        if path.startswith("/api/v0/"):
            path = path.replace("/api/v0", "", 1)
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        async with httpx.AsyncClient(
            timeout=self.timeout,
            auth=httpx.BasicAuth(self.api_key, self.api_secret),
        ) as client:
            return await client.get(url, params=params)

    async def _paginate(
        self,
        path: str,
        params: Dict[str, Any],
        max_pages: int = 4,
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        next_path = path
        next_params = dict(params)
        for _ in range(max(1, max_pages)):
            payload = await self._get_json(next_path, next_params)
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
            page_items = payload.get("items") if isinstance(payload, dict) else []
            if isinstance(page_items, list):
                items.extend(item for item in page_items if isinstance(item, dict))
            next_page_path = payload.get("nextPagePath") if isinstance(payload, dict) else None
            if not next_page_path:
                break
            next_path = str(next_page_path)
            next_params = {}
        return items
