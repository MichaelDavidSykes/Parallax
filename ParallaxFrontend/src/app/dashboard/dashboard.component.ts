import { Component, OnInit } from '@angular/core';
import { forkJoin } from 'rxjs';

import { BacktestRun, HealthResponse, Holding, Market, NetWorthSummary, Opportunity, PlatformValue, Portfolio } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  public loading = false;
  public error = '';
  public health: HealthResponse | null = null;
  public markets: Market[] = [];
  public opportunities: Opportunity[] = [];
  public backtests: BacktestRun[] = [];
  public portfolios: Portfolio[] = [];
  public netWorth: NetWorthSummary | null = null;

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  public refresh(): void {
    this.loading = true;
    this.error = '';
    forkJoin({
      health: this.api.health(),
      markets: this.api.listMarkets(40),
      opportunities: this.api.listOpportunities(20),
      backtests: this.api.listBacktests(10),
      portfolios: this.api.listPortfolios(),
      netWorth: this.api.accountSummary()
    }).subscribe({
      next: result => {
        this.health = result.health;
        this.markets = result.markets;
        this.opportunities = result.opportunities;
        this.backtests = result.backtests;
        this.portfolios = result.portfolios;
        this.netWorth = result.netWorth;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Parallax API is not reachable.';
        this.loading = false;
      }
    });
  }

  public get bestOpportunity(): Opportunity | null {
    return this.opportunities[0] || null;
  }

  public get paperCash(): number {
    return this.portfolios.reduce((total, portfolio) => total + portfolio.cash_balance, 0);
  }

  public get platforms(): PlatformValue[] {
    return this.netWorth?.platforms || [];
  }

  public get stockPerformance(): Holding[] {
    return this.netWorth?.stock_performance || [];
  }

  public get lastBacktest(): BacktestRun | null {
    return this.backtests[0] || null;
  }

  public pct(value: number | undefined): string {
    return `${(((value || 0) * 100)).toFixed(1)}%`;
  }

  public signedPct(value: number | undefined): string {
    const pct = value || 0;
    return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`;
  }
}
