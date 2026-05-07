import { Component, OnInit } from '@angular/core';

import { Market, Portfolio, Trade } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-simulator',
  templateUrl: './simulator.component.html',
  styleUrls: ['./simulator.component.scss']
})
export class SimulatorComponent implements OnInit {
  public portfolios: Portfolio[] = [];
  public markets: Market[] = [];
  public trades: Trade[] = [];
  public loading = false;
  public error = '';
  public createForm = {
    name: 'Paper Alpha',
    initialCash: 10000
  };
  public tradeForm = {
    portfolioId: '',
    marketId: '',
    side: 'BUY',
    outcome: 'YES',
    quantity: 10,
    price: 0.5,
    fees: 0,
    strategy: 'manual'
  };

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  public refresh(): void {
    this.loading = true;
    this.error = '';
    this.api.listMarkets(100).subscribe({
      next: markets => {
        this.markets = markets;
        if (!this.tradeForm.marketId && markets.length) {
          this.tradeForm.marketId = markets[0].id;
          this.applySelectedMarketPrice();
        }
        this.loadPortfolios();
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load simulator data.';
        this.loading = false;
      }
    });
  }

  public loadPortfolios(): void {
    this.api.listPortfolios().subscribe({
      next: portfolios => {
        this.portfolios = portfolios;
        if (!this.tradeForm.portfolioId && portfolios.length) {
          this.tradeForm.portfolioId = portfolios[0].id;
        }
        this.loadTrades();
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load portfolios.';
        this.loading = false;
      }
    });
  }

  public loadTrades(): void {
    this.api.listTrades(this.tradeForm.portfolioId, 80).subscribe({
      next: trades => {
        this.trades = trades;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load trades.';
        this.loading = false;
      }
    });
  }

  public createPortfolio(): void {
    this.loading = true;
    this.error = '';
    this.api.createPortfolio(this.createForm.name, this.createForm.initialCash).subscribe({
      next: portfolio => {
        this.portfolios = [portfolio, ...this.portfolios];
        this.tradeForm.portfolioId = portfolio.id;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not create portfolio.';
        this.loading = false;
      }
    });
  }

  public simulate(): void {
    this.loading = true;
    this.error = '';
    this.api.simulateTrade({
      portfolio_id: this.tradeForm.portfolioId,
      market_id: this.tradeForm.marketId,
      side: this.tradeForm.side,
      outcome: this.tradeForm.outcome,
      quantity: this.tradeForm.quantity,
      price: this.tradeForm.price,
      fees: this.tradeForm.fees,
      strategy: this.tradeForm.strategy
    }).subscribe({
      next: trade => {
        this.trades = [trade, ...this.trades];
        this.loadPortfolios();
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not simulate trade.';
        this.loading = false;
      }
    });
  }

  public applySelectedMarketPrice(): void {
    const selected = this.markets.find(market => market.id === this.tradeForm.marketId);
    if (!selected) {
      return;
    }
    const yesPrice = selected.outcome_prices[0] || 0.5;
    this.tradeForm.price = this.tradeForm.outcome === 'YES' ? yesPrice : 1 - yesPrice;
  }

  public get selectedPortfolio(): Portfolio | null {
    return this.portfolios.find(portfolio => portfolio.id === this.tradeForm.portfolioId) || null;
  }
}

