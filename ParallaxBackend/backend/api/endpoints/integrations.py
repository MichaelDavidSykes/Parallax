from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from backend.core.config import settings
from backend.integrations.binance import BinanceClient
from backend.integrations.trading212 import Trading212Client, Trading212NotConfigured
from backend.models.schemas import BinanceTickerOut, IntegrationStatus, Trading212AccountOut
from backend.services.integration_service import IntegrationService

router = APIRouter()


@router.get("", response_model=list[IntegrationStatus])
async def list_integrations():
    return await IntegrationService().statuses()


@router.get("/binance/prices", response_model=list[BinanceTickerOut])
async def binance_prices(symbols: str = Query(default="")):
    requested_symbols = [symbol.strip() for symbol in symbols.split(",") if symbol.strip()]
    if not requested_symbols:
        requested_symbols = settings.binance_symbols
    try:
        return await BinanceClient(settings.BINANCE_API_URL).ticker_prices(requested_symbols)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Binance rejected the request.",
        ) from exc


@router.get("/trading212/account", response_model=Trading212AccountOut)
async def trading212_account():
    client = Trading212Client(
        settings.trading212_base_url,
        settings.TRADING212_API_KEY,
        settings.TRADING212_API_SECRET,
    )
    try:
        return await client.account_snapshot()
    except Trading212NotConfigured as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Trading 212 rejected the request.",
        ) from exc
