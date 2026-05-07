export interface HealthResponse {
  status: string;
  service: string;
  db_path: string;
}

export interface IntegrationStatus {
  name: string;
  configured: boolean;
  status: string;
  endpoint?: string;
}

export interface PlatformValue {
  platform: string;
  configured: boolean;
  status: string;
  currency: string;
  cash: number;
  positions_value: number;
  total_value: number;
}

export interface Holding {
  platform: string;
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  avg_price?: number;
  current_price?: number;
  value: number;
  day_change_pct?: number;
  total_return_pct?: number;
  total_return_value?: number;
}

export interface NetWorthSummary {
  currency: string;
  total_value: number;
  cash: number;
  positions_value: number;
  platforms: PlatformValue[];
  holdings: Holding[];
  stock_performance: Holding[];
  updated_at: string;
}

export interface Trading212Position {
  symbol: string;
  name: string;
  currency: string;
  quantity: number;
  avg_price?: number;
  current_price?: number;
  value: number;
  pnl: number;
  pnl_pct?: number;
}

export interface Trading212Trade {
  id: string;
  symbol: string;
  name: string;
  side: 'BUY' | 'SELL' | string;
  quantity: number;
  price: number;
  value: number;
  status: string;
  type: string;
  executed_at: string;
}

export interface Trading212Summary {
  configured: boolean;
  status: string;
  platform: string;
  currency: string;
  cash: number;
  positions_value: number;
  total_value: number;
  total_pnl: number;
  total_pnl_pct?: number;
  positions: Trading212Position[];
  trades: Trading212Trade[];
  updated_at: string;
}

export interface ChartCandle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface ChartPoint {
  time: number;
  value: number;
}

export interface TradingChart {
  configured: boolean;
  status: string;
  ticker: string;
  timeframe: string;
  candles: ChartCandle[];
  line: ChartPoint[];
  trades: Trading212Trade[];
}

export interface Automation {
  id: string;
  name: string;
  status: string;
  trigger: string;
  action: string;
  updated_at: string;
}
