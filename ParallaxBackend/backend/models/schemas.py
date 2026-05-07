from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MarketOut(BaseModel):
    id: str
    question: str
    slug: Optional[str] = ""
    category: Optional[str] = ""
    active: bool = True
    closed: bool = False
    end_date: Optional[str] = None
    liquidity: float = 0
    volume: float = 0
    image: Optional[str] = ""
    outcomes: List[str] = []
    outcome_prices: List[float] = []
    clob_token_ids: List[str] = []
    updated_at: str


class SyncMarketsResponse(BaseModel):
    fetched: int
    stored: int
    markets: List[MarketOut]


class SnapshotOut(BaseModel):
    id: Optional[int] = None
    market_id: str
    captured_at: str
    yes_price: float
    no_price: float
    fair_probability: float
    confidence: float
    source: str
    liquidity: float = 0
    volume: float = 0


class OpportunityOut(BaseModel):
    id: Optional[int] = None
    market_id: str
    question: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    detected_at: str
    side: str
    market_price: float
    fair_probability: float
    edge: float
    expected_value: float
    confidence: float
    max_stake: float
    rationale: str


class OpportunityScanRequest(BaseModel):
    market_limit: int = Field(default=80, ge=1, le=500)
    min_edge: float = Field(default=0.04, ge=0, le=1)
    refresh_markets: bool = True


class OpportunityScanResponse(BaseModel):
    scanned: int
    created: int
    opportunities: List[OpportunityOut]


class PortfolioCreate(BaseModel):
    name: str = "Paper Alpha"
    initial_cash: float = Field(default=10000, gt=0)


class PositionOut(BaseModel):
    id: Optional[int] = None
    portfolio_id: str
    market_id: str
    outcome: str
    quantity: float
    avg_price: float
    realized_pnl: float = 0


class PortfolioOut(BaseModel):
    id: str
    name: str
    initial_cash: float
    cash_balance: float
    created_at: str
    positions: List[PositionOut] = []


class SimulatedTradeCreate(BaseModel):
    portfolio_id: str
    market_id: str
    side: str = Field(default="BUY", pattern="^(BUY|SELL|buy|sell)$")
    outcome: str = "YES"
    quantity: float = Field(default=10, gt=0)
    price: float = Field(default=0.5, ge=0.01, le=0.99)
    fees: float = Field(default=0, ge=0)
    strategy: str = "manual"
    metadata: Dict[str, Any] = {}


class TradeOut(BaseModel):
    id: Optional[int] = None
    portfolio_id: str
    market_id: str
    side: str
    outcome: str
    quantity: float
    price: float
    notional: float
    fees: float = 0
    simulated_at: Optional[str] = None
    strategy: str = "manual"
    metadata: Dict[str, Any] = {}


class BacktestCreate(BaseModel):
    name: str = "Stat arb replay"
    strategy: str = "stat_arb_v1"
    model_id: str = "stat_arb_v1"
    initial_cash: float = Field(default=10000, gt=0)
    market_limit: int = Field(default=100, ge=1, le=1000)
    min_edge: float = Field(default=0.04, ge=0, le=1)
    max_position_pct: float = Field(default=0.08, gt=0, le=1)
    fee_bps: float = Field(default=0, ge=0)
    slippage_bps: float = Field(default=0, ge=0)
    valuation_basis: str = Field(default="fair", pattern="^(fair|market|hybrid)$")
    refresh_markets: bool = True


class BacktestOut(BaseModel):
    id: str
    name: str
    strategy: str
    model_id: Optional[str] = None
    initial_cash: float
    final_equity: float
    return_pct: float
    started_at: str
    completed_at: str
    parameters: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    equity_curve: List[Dict[str, Any]] = []
    trades: List[Dict[str, Any]] = []


class IntegrationStatus(BaseModel):
    name: str
    configured: bool
    status: str
    endpoint: Optional[str] = ""


class BinanceTickerOut(BaseModel):
    symbol: str
    price: float
    source: str = "binance-spot"


class Trading212AccountOut(BaseModel):
    info: Dict[str, Any] = {}
    cash: Dict[str, Any] = {}
    positions: List[Dict[str, Any]] = []
    source: str = "trading212"


class PlatformValueOut(BaseModel):
    platform: str
    configured: bool
    status: str
    currency: str = "USD"
    cash: float = 0
    positions_value: float = 0
    total_value: float = 0


class HoldingOut(BaseModel):
    platform: str
    symbol: str
    name: str = ""
    asset_type: str = "asset"
    quantity: float = 0
    avg_price: Optional[float] = None
    current_price: Optional[float] = None
    value: float = 0
    day_change_pct: Optional[float] = None
    total_return_pct: Optional[float] = None
    total_return_value: Optional[float] = None


class NetWorthSummaryOut(BaseModel):
    currency: str = "USD"
    total_value: float
    cash: float = 0
    positions_value: float = 0
    platforms: List[PlatformValueOut] = []
    holdings: List[HoldingOut] = []
    stock_performance: List[HoldingOut] = []
    updated_at: str


class ModelParameterOut(BaseModel):
    key: str
    label: str
    kind: str = "number"
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    options: List[str] = []


class BacktestModelOut(BaseModel):
    id: str
    name: str
    description: str = ""
    runtime: str = "builtin"
    image: str = ""
    strategy: str = "stat_arb_v1"
    status: str = "available"
    parameters: List[ModelParameterOut] = []
