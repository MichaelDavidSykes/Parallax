import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { BacktestModel, BacktestRun, BinanceTicker, HealthResponse, IntegrationStatus, Market, NetWorthSummary, Opportunity, Portfolio, Trade, Trading212Account } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ParallaxApiService {
  private readonly baseUrl = `${environment.apiUrl}/api/${environment.apiVersion}`;

  constructor(private http: HttpClient) {}

  health(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`);
  }

  listMarkets(limit = 100): Observable<Market[]> {
    return this.http.get<Market[]>(`${this.baseUrl}/markets`, {
      params: { limit }
    });
  }

  syncMarkets(limit = 80): Observable<{ fetched: number; stored: number; markets: Market[] }> {
    return this.http.post<{ fetched: number; stored: number; markets: Market[] }>(
      `${this.baseUrl}/markets/sync`,
      {},
      { params: { limit } }
    );
  }

  listOpportunities(limit = 100): Observable<Opportunity[]> {
    return this.http.get<Opportunity[]>(`${this.baseUrl}/opportunities`, {
      params: { limit }
    });
  }

  scanOpportunities(marketLimit = 80, minEdge = 0.04, refreshMarkets = true): Observable<{ scanned: number; created: number; opportunities: Opportunity[] }> {
    return this.http.post<{ scanned: number; created: number; opportunities: Opportunity[] }>(
      `${this.baseUrl}/opportunities/scan`,
      {
        market_limit: marketLimit,
        min_edge: minEdge,
        refresh_markets: refreshMarkets
      }
    );
  }

  listPortfolios(): Observable<Portfolio[]> {
    return this.http.get<Portfolio[]>(`${this.baseUrl}/portfolios`);
  }

  createPortfolio(name: string, initialCash: number): Observable<Portfolio> {
    return this.http.post<Portfolio>(`${this.baseUrl}/portfolios`, {
      name,
      initial_cash: initialCash
    });
  }

  simulateTrade(payload: {
    portfolio_id: string;
    market_id: string;
    side: string;
    outcome: string;
    quantity: number;
    price: number;
    fees: number;
    strategy: string;
  }): Observable<Trade> {
    return this.http.post<Trade>(`${this.baseUrl}/portfolios/trades`, payload);
  }

  listTrades(portfolioId = '', limit = 200): Observable<Trade[]> {
    return this.http.get<Trade[]>(`${this.baseUrl}/portfolios/trades`, {
      params: { portfolio_id: portfolioId, limit }
    });
  }

  listBacktests(limit = 50): Observable<BacktestRun[]> {
    return this.http.get<BacktestRun[]>(`${this.baseUrl}/backtests`, {
      params: { limit }
    });
  }

  runBacktest(payload: {
    name: string;
    strategy: string;
    model_id: string;
    initial_cash: number;
    market_limit: number;
    min_edge: number;
    max_position_pct: number;
    fee_bps: number;
    slippage_bps: number;
    valuation_basis: string;
    refresh_markets: boolean;
  }): Observable<BacktestRun> {
    return this.http.post<BacktestRun>(`${this.baseUrl}/backtests`, payload);
  }

  listBacktestModels(): Observable<BacktestModel[]> {
    return this.http.get<BacktestModel[]>(`${this.baseUrl}/backtests/models`);
  }

  accountSummary(): Observable<NetWorthSummary> {
    return this.http.get<NetWorthSummary>(`${this.baseUrl}/accounts/summary`);
  }

  integrations(): Observable<IntegrationStatus[]> {
    return this.http.get<IntegrationStatus[]>(`${this.baseUrl}/integrations`);
  }

  binancePrices(symbols = ''): Observable<BinanceTicker[]> {
    return this.http.get<BinanceTicker[]>(`${this.baseUrl}/integrations/binance/prices`, {
      params: symbols ? { symbols } : {}
    });
  }

  trading212Account(): Observable<Trading212Account> {
    return this.http.get<Trading212Account>(`${this.baseUrl}/integrations/trading212/account`);
  }
}
