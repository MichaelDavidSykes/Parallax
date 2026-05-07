from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from backend.integrations.trading212 import Trading212NotConfigured
from backend.models.schemas import MarketOrderCreate, Trading212SummaryOut, TradingChartOut
from backend.services.trading212_service import Trading212Service

router = APIRouter()


@router.get("/summary", response_model=Trading212SummaryOut)
async def summary():
    return await Trading212Service().summary()


@router.get("/chart", response_model=TradingChartOut)
async def chart(
    ticker: str = Query(default=""),
    timeframe: str = Query(default="1M", pattern="^(1D|1W|1M|3M|1Y|ALL)$"),
):
    return await Trading212Service().chart(ticker=ticker, timeframe=timeframe)


@router.post("/orders/market")
async def market_order(request: MarketOrderCreate):
    try:
        return await Trading212Service().market_order(
            ticker=request.ticker,
            side=request.side,
            quantity=request.quantity,
            extended_hours=request.extended_hours,
        )
    except Trading212NotConfigured as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Trading 212 rejected the order.",
        ) from exc
