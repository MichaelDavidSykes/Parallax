import { Component, OnInit } from '@angular/core';

import { BacktestRun } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-backtests',
  templateUrl: './backtests.component.html',
  styleUrls: ['./backtests.component.scss']
})
export class BacktestsComponent implements OnInit {
  public runs: BacktestRun[] = [];
  public loading = false;
  public error = '';
  public form = {
    name: 'Stat arb replay',
    strategy: 'stat_arb_v1',
    initial_cash: 10000,
    market_limit: 100,
    min_edge: 0.04,
    max_position_pct: 0.08,
    fee_bps: 0,
    refresh_markets: true
  };

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.load();
  }

  public load(): void {
    this.loading = true;
    this.error = '';
    this.api.listBacktests(50).subscribe({
      next: runs => {
        this.runs = runs;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load backtests.';
        this.loading = false;
      }
    });
  }

  public run(): void {
    this.loading = true;
    this.error = '';
    this.api.runBacktest(this.form).subscribe({
      next: run => {
        this.runs = [run, ...this.runs];
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not run backtest.';
        this.loading = false;
      }
    });
  }

  public metric(run: BacktestRun, key: string): number {
    return Number(run.metrics[key] || 0);
  }
}

