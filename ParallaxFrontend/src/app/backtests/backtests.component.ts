import { Component, OnInit } from '@angular/core';

import { BacktestModel, BacktestRun } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-backtests',
  templateUrl: './backtests.component.html',
  styleUrls: ['./backtests.component.scss']
})
export class BacktestsComponent implements OnInit {
  public runs: BacktestRun[] = [];
  public models: BacktestModel[] = [];
  public loading = false;
  public error = '';
  public form = {
    name: 'Stat arb replay',
    strategy: 'stat_arb_v1',
    model_id: 'stat_arb_v1',
    initial_cash: 10000,
    market_limit: 100,
    min_edge: 0.04,
    max_position_pct: 0.08,
    fee_bps: 0,
    slippage_bps: 0,
    valuation_basis: 'fair',
    refresh_markets: true
  };

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.load();
    this.loadModels();
  }

  public loadModels(): void {
    this.api.listBacktestModels().subscribe({
      next: models => {
        this.models = models;
        if (models.length && !models.some(model => model.id === this.form.model_id)) {
          this.selectModel(models[0]);
        }
      },
      error: () => {
        this.models = [];
      }
    });
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

  public selectModel(model: BacktestModel): void {
    this.form.model_id = model.id;
    this.form.strategy = model.strategy;
    model.parameters.forEach(parameter => {
      if (parameter.key in this.form) {
        (this.form as Record<string, string | number | boolean>)[parameter.key] = parameter.default;
      }
    });
  }

  public onModelChange(modelId: string): void {
    const model = this.models.find(item => item.id === modelId);
    if (model) {
      this.selectModel(model);
    }
  }
}
