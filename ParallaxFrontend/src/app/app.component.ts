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
    { label: 'Trading', route: '/trading', icon: 'fa-chart-simple' },
    { label: 'Automations', route: '/automations', icon: 'fa-bolt' }
  ];
}
