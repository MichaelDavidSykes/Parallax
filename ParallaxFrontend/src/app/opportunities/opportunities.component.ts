import { Component, OnInit } from '@angular/core';

import { Opportunity } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-opportunities',
  templateUrl: './opportunities.component.html',
  styleUrls: ['./opportunities.component.scss']
})
export class OpportunitiesComponent implements OnInit {
  public opportunities: Opportunity[] = [];
  public loading = false;
  public error = '';
  public marketLimit = 80;
  public minEdge = 0.04;

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.load();
  }

  public load(): void {
    this.loading = true;
    this.error = '';
    this.api.listOpportunities(100).subscribe({
      next: opportunities => {
        this.opportunities = opportunities;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not load opportunities.';
        this.loading = false;
      }
    });
  }

  public scan(): void {
    this.loading = true;
    this.error = '';
    this.api.scanOpportunities(this.marketLimit, this.minEdge, true).subscribe({
      next: response => {
        this.opportunities = response.opportunities;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Could not scan markets.';
        this.loading = false;
      }
    });
  }

  public abs(value: number): number {
    return Math.abs(value);
  }
}

