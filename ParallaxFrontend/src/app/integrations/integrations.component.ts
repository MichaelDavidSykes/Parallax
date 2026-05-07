import { Component, OnInit } from '@angular/core';

import { BinanceTicker, IntegrationStatus, Trading212Account } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-integrations',
  templateUrl: './integrations.component.html',
  styleUrls: ['./integrations.component.scss']
})
export class IntegrationsComponent implements OnInit {
  public statuses: IntegrationStatus[] = [];
  public binancePrices: BinanceTicker[] = [];
  public trading212Account: Trading212Account | null = null;
  public loading = false;
  public error = '';

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  public refresh(): void {
    this.loading = true;
    this.error = '';
    this.binancePrices = [];
    this.trading212Account = null;
    this.api.integrations().subscribe({
      next: statuses => {
        this.statuses = statuses;
        this.loadBinancePrices();
        if (statuses.some(status => status.name === 'Trading 212' && status.configured)) {
          this.loadTrading212Account();
        }
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load integration status.';
        this.loading = false;
      }
    });
  }

  private loadBinancePrices(): void {
    this.api.binancePrices().subscribe({
      next: prices => {
        this.binancePrices = prices;
      },
      error: () => {
        this.binancePrices = [];
      }
    });
  }

  private loadTrading212Account(): void {
    this.api.trading212Account().subscribe({
      next: account => {
        this.trading212Account = account;
      },
      error: () => {
        this.trading212Account = null;
      }
    });
  }

  public statusClass(status: IntegrationStatus): string {
    if (!status.configured) {
      return 'status-dot--off';
    }
    return status.status === 'online' || status.status === 'enabled' || status.status === 'configured'
      ? 'status-dot--ok'
      : 'status-dot--warn';
  }

  public cashValue(key: string): number {
    return Number(this.trading212Account?.cash?.[key] ?? 0);
  }
}
