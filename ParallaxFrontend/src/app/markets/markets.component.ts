import { Component, OnInit } from '@angular/core';

import { Market } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-markets',
  templateUrl: './markets.component.html',
  styleUrls: ['./markets.component.scss']
})
export class MarketsComponent implements OnInit {
  public markets: Market[] = [];
  public loading = false;
  public error = '';
  public limit = 80;

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.load();
  }

  public load(): void {
    this.loading = true;
    this.error = '';
    this.api.listMarkets(this.limit).subscribe({
      next: markets => {
        this.markets = markets;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load markets.';
        this.loading = false;
      }
    });
  }

  public sync(): void {
    this.loading = true;
    this.error = '';
    this.api.syncMarkets(this.limit).subscribe({
      next: response => {
        this.markets = response.markets;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not sync Polymarket.';
        this.loading = false;
      }
    });
  }

  public yesPrice(market: Market): number {
    return market.outcome_prices[0] || 0;
  }
}

