export interface Market {
  id: string;
  question: string;
  slug?: string;
  category?: string;
  active: boolean;
  closed: boolean;
  end_date?: string;
  liquidity: number;
  volume: number;
  image?: string;
  outcomes: string[];
  outcome_prices: number[];
  clob_token_ids: string[];
  updated_at: string;
}

export interface Opportunity {
  id?: number;
  market_id: string;
  question?: string;
  slug?: string;
  category?: string;
  detected_at: string;
  side: string;
  market_price: number;
  fair_probability: number;
  edge: number;
  expected_value: number;
  confidence: number;
  max_stake: number;
  rationale: string;
}

export interface Portfolio {
  id: string;
  name: string;
  initial_cash: number;
  cash_balance: number;
  created_at: string;
  positions: Position[];
}

export interface Position {
  id?: number;
  portfolio_id: string;
  market_id: string;
  outcome: string;
  quantity: number;
  avg_price: number;
  realized_pnl: number;
}

export interface Trade {
  id?: number;
  portfolio_id: string;
  market_id: string;
  side: string;
  outcome: string;
  quantity: number;
  price: number;
  notional: number;
  fees: number;
  simulated_at?: string;
  strategy: string;
}

export interface BacktestRun {
  id: string;
  name: string;
  strategy: string;
  initial_cash: number;
  final_equity: number;
  return_pct: number;
  started_at: string;
  completed_at: string;
  parameters: Record<string, unknown>;
  metrics: Record<string, number>;
  equity_curve: Array<{ timestamp: string; cash: number; equity: number }>;
  trades: Array<Record<string, unknown>>;
}

export interface IntegrationStatus {
  name: string;
  configured: boolean;
  status: string;
  endpoint?: string;
}

export interface BinanceTicker {
  symbol: string;
  price: number;
  source: string;
}

export interface Trading212Account {
  info: Record<string, unknown>;
  cash: Record<string, number>;
  positions: Array<Record<string, unknown>>;
  source: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  db_path: string;
}
