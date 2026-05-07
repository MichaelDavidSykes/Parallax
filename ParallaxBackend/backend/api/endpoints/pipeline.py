from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_database
from backend.db.database import Database
from backend.models.schemas import OpportunityScanRequest, OpportunityScanResponse
from backend.services.opportunity_service import OpportunityService

router = APIRouter()


@router.post("/ingest-and-scan", response_model=OpportunityScanResponse)
async def ingest_and_scan(
    request: OpportunityScanRequest,
    db: Database = Depends(get_database),
):
    return await OpportunityService(db).scan(
        market_limit=request.market_limit,
        min_edge=request.min_edge,
        refresh_markets=True,
    )

