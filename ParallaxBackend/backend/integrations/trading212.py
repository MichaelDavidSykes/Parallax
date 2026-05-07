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
            response = await self._get("/equity/account/info")
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
        response = await self._get("/equity/account/info")
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    async def account_cash(self) -> Dict[str, Any]:
        response = await self._get("/equity/account/cash")
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    async def portfolio(self) -> List[Dict[str, Any]]:
        response = await self._get("/equity/portfolio")
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else []

    async def account_snapshot(self) -> Dict[str, Any]:
        return {
            "info": await self.account_info(),
            "cash": await self.account_cash(),
            "positions": await self.portfolio(),
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
