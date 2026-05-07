import { Component, OnInit } from '@angular/core';

import { Automation } from '../models/api.models';
import { ParallaxApiService } from '../services/parallax-api.service';

@Component({
  selector: 'app-automations',
  templateUrl: './automations.component.html',
  styleUrls: ['./automations.component.scss']
})
export class AutomationsComponent implements OnInit {
  public automations: Automation[] = [];
  public loading = false;
  public error = '';

  constructor(private api: ParallaxApiService) {}

  ngOnInit(): void {
    this.load();
  }

  public load(): void {
    this.loading = true;
    this.error = '';
    this.api.automations().subscribe({
      next: automations => {
        this.automations = automations;
        this.loading = false;
      },
      error: err => {
        this.error = err?.error?.detail || err?.message || 'Automations are not reachable.';
        this.loading = false;
      }
    });
  }
}
