import { Component, OnInit } from '@angular/core';
import { forkJoin } from 'rxjs';

import { BacktestRun, HealthResponse, Market, Opportunity, Portfolio } from '../models/api.models';
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
      portfolios: this.api.listPortfolios()
    }).subscribe({
      next: result => {
        this.health = result.health;
        this.markets = result.markets;
        this.opportunities = result.opportunities;
        this.backtests = result.backtests;
        this.portfolios = result.portfolios;
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

  public get lastBacktest(): BacktestRun | null {
    return this.backtests[0] || null;
  }

  public pct(value: number | undefined): string {
    return `${(((value || 0) * 100)).toFixed(1)}%`;
  }
}

