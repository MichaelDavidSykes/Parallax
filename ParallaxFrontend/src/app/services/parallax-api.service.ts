import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Automation, HealthResponse, IntegrationStatus, NetWorthSummary, Trading212Summary, TradingChart } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ParallaxApiService {
  private readonly baseUrl = `${environment.apiUrl}/api/${environment.apiVersion}`;

  constructor(private http: HttpClient) {}

  health(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`);
  }

  accountSummary(): Observable<NetWorthSummary> {
    return this.http.get<NetWorthSummary>(`${this.baseUrl}/accounts/summary`);
  }

  trading212Summary(): Observable<Trading212Summary> {
    return this.http.get<Trading212Summary>(`${this.baseUrl}/trading212/summary`);
  }

  tradingChart(ticker = '', timeframe = '1M'): Observable<TradingChart> {
    return this.http.get<TradingChart>(`${this.baseUrl}/trading212/chart`, {
      params: { ticker, timeframe }
    });
  }

  placeMarketOrder(payload: {
    ticker: string;
    side: string;
    quantity: number;
    extended_hours: boolean;
  }): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.baseUrl}/trading212/orders/market`, payload);
  }

  automations(): Observable<Automation[]> {
    return this.http.get<Automation[]>(`${this.baseUrl}/automations`);
  }

  integrations(): Observable<IntegrationStatus[]> {
    return this.http.get<IntegrationStatus[]>(`${this.baseUrl}/integrations`);
  }
}
