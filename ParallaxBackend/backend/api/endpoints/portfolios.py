from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies import get_database
from backend.db.database import Database
from backend.models.schemas import PortfolioCreate, PortfolioOut, SimulatedTradeCreate, TradeOut
from backend.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("", response_model=list[PortfolioOut])
def list_portfolios(db: Database = Depends(get_database)):
    portfolios = PortfolioService(db).list()
    if not portfolios:
        portfolios = [PortfolioService(db).get_or_create_default()]
    return portfolios


@router.post("", response_model=PortfolioOut)
def create_portfolio(request: PortfolioCreate, db: Database = Depends(get_database)):
    return PortfolioService(db).create(
        name=request.name,
        initial_cash=request.initial_cash,
    )


@router.post("/trades", response_model=TradeOut)
def simulate_trade(request: SimulatedTradeCreate, db: Database = Depends(get_database)):
    try:
        return PortfolioService(db).trade(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trades", response_model=list[TradeOut])
def list_trades(
    portfolio_id: str = "",
    limit: int = Query(default=200, ge=1, le=1000),
    db: Database = Depends(get_database),
):
    return PortfolioService(db).list_trades(
        portfolio_id=portfolio_id or None,
        limit=limit,
    )

