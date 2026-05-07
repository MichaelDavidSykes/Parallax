import { Component, OnInit } from '@angular/core';

import { IntegrationStatus } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-integrations',
  templateUrl: './integrations.component.html',
  styleUrls: ['./integrations.component.scss']
})
export class IntegrationsComponent implements OnInit {
  public statuses: IntegrationStatus[] = [];
  public loading = false;
  public error = '';

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.refresh();
  }

  public refresh(): void {
    this.loading = true;
    this.error = '';
    this.api.integrations().subscribe({
      next: statuses => {
        this.statuses = statuses;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load integration status.';
        this.loading = false;
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
}

