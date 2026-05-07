import { Component, OnInit } from '@angular/core';
import { forkJoin } from 'rxjs';

import { HealthResponse, Trading212Summary, Trading212Trade } from '../models/api.models';
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
  public summary: Trading212Summary | null = null;

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  public refresh(): void {
    this.loading = true;
    this.error = '';
    forkJoin({
      health: this.api.health(),
      summary: this.api.trading212Summary()
    }).subscribe({
      next: result => {
        this.health = result.health;
        this.summary = result.summary;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Trading 212 is not reachable.';
        this.loading = false;
      }
    });
  }

  public get positions() {
    return this.summary?.positions || [];
  }

  public get trades(): Trading212Trade[] {
    return this.summary?.trades || [];
  }

  public get currency(): string {
    return this.summary?.currency || 'USD';
  }

  public signedPct(value: number | undefined | null): string {
    if (value === null || value === undefined) {
      return '-';
    }
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  }

  public signedMoney(value: number | undefined | null): string {
    const amount = value || 0;
    return `${amount >= 0 ? '+' : '-'}${this.currencySymbol}${Math.abs(amount).toLocaleString(undefined, {
      maximumFractionDigits: 2
    })}`;
  }

  public get currencySymbol(): string {
    return this.currency === 'GBP' ? '£' : this.currency === 'EUR' ? '€' : '$';
  }
}
