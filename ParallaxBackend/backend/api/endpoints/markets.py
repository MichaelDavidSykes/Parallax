from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import get_database
from backend.db.database import Database
from backend.models.schemas import MarketOut, SyncMarketsResponse
from backend.services.market_service import MarketService

router = APIRouter()


@router.get("", response_model=list[MarketOut])
def list_markets(
    limit: int = Query(default=100, ge=1, le=500),
    active_only: bool = True,
    db: Database = Depends(get_database),
):
    return MarketService(db).list_markets(limit=limit, active_only=active_only)


@router.post("/sync", response_model=SyncMarketsResponse)
async def sync_markets(
    limit: int = Query(default=80, ge=1, le=500),
    db: Database = Depends(get_database),
):
    return await MarketService(db).sync_markets(limit=limit)

