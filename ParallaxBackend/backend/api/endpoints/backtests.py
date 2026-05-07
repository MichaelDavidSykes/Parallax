from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies import get_database
from backend.db.database import Database
from backend.models.schemas import BacktestCreate, BacktestOut
from backend.services.backtest_service import BacktestService

router = APIRouter()


@router.get("", response_model=list[BacktestOut])
def list_backtests(
    limit: int = Query(default=50, ge=1, le=200),
    db: Database = Depends(get_database),
):
    return BacktestService(db).list(limit=limit)


@router.post("", response_model=BacktestOut)
async def run_backtest(request: BacktestCreate, db: Database = Depends(get_database)):
    try:
        return await BacktestService(db).run(
            name=request.name,
            strategy=request.strategy,
            initial_cash=request.initial_cash,
            market_limit=request.market_limit,
            min_edge=request.min_edge,
            max_position_pct=request.max_position_pct,
            fee_bps=request.fee_bps,
            refresh_markets=request.refresh_markets,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

