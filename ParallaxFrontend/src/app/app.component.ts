import { Component } from '@angular/core';

interface NavItem {
  label: string;
  route: string;
  icon: string;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  public title = 'Parallax';
  public readonly navItems: NavItem[] = [
    { label: 'Dashboard', route: '/dashboard', icon: 'fa-chart-line' },
    { label: 'Markets', route: '/markets', icon: 'fa-layer-group' },
    { label: 'Scanner', route: '/opportunities', icon: 'fa-bullseye' },
    { label: 'Backtest', route: '/backtests', icon: 'fa-flask' },
    { label: 'Sim', route: '/simulator', icon: 'fa-play' },
    { label: 'Integrations', route: '/integrations', icon: 'fa-plug' }
  ];
}
