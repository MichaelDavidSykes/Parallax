from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.dependencies import get_database
from backend.db.database import Database
from backend.models.schemas import (
    OpportunityOut,
    OpportunityScanRequest,
    OpportunityScanResponse,
)
from backend.services.opportunity_service import OpportunityService

router = APIRouter()


@router.get("", response_model=list[OpportunityOut])
def list_opportunities(
    limit: int = Query(default=100, ge=1, le=500),
    db: Database = Depends(get_database),
):
    return OpportunityService(db).list_opportunities(limit=limit)


@router.post("/scan", response_model=OpportunityScanResponse)
async def scan_opportunities(
    request: OpportunityScanRequest,
    db: Database = Depends(get_database),
):
    return await OpportunityService(db).scan(
        market_limit=request.market_limit,
        min_edge=request.min_edge,
        refresh_markets=request.refresh_markets,
    )

