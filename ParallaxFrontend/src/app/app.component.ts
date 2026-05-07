import { Component } from '@angular/core';
import { Router } from '@angular/router';

interface NavItem {
  label: string;
  route: string;
  icon: string;
}

interface NavSection {
  id: string;
  label: string;
  icon: string;
  items: NavItem[];
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  public title = 'Parallax';
  public navHidden = false;
  public navSearch = '';
  public expandedNavSectionId: string | null = 'trading';
  public readonly navSections: NavSection[] = [
    {
      id: 'trading',
      label: 'Trading',
      icon: 'fa-chart-line',
      items: [
        { label: 'Dashboard', route: '/dashboard', icon: 'fa-gauge-high' },
        { label: 'Markets', route: '/markets', icon: 'fa-layer-group' },
        { label: 'Opportunities', route: '/opportunities', icon: 'fa-scale-balanced' }
      ]
    },
    {
      id: 'research',
      label: 'Research',
      icon: 'fa-flask',
      items: [
        { label: 'Backtests', route: '/backtests', icon: 'fa-clock-rotate-left' },
        { label: 'Simulator', route: '/simulator', icon: 'fa-wallet' }
      ]
    },
    {
      id: 'ops',
      label: 'Ops',
      icon: 'fa-plug',
      items: [
        { label: 'Integrations', route: '/integrations', icon: 'fa-diagram-project' }
      ]
    }
  ];

  constructor(private router: Router) {}

  public toggleSidebar(): void {
    this.navHidden = !this.navHidden;
    window.requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
  }

  public get filteredNavSections(): NavSection[] {
    const query = this.navSearch.trim().toLowerCase();
    if (!query) {
      return this.navSections;
    }
    return this.navSections
      .map(section => ({
        ...section,
        items: section.items.filter(item =>
          section.label.toLowerCase().includes(query) ||
          item.label.toLowerCase().includes(query)
        )
      }))
      .filter(section => section.items.length > 0);
  }

  public isNavItemActive(route: string): boolean {
    const path = this.router.url.split('?')[0].split('#')[0];
    return path === route || path.startsWith(`${route}/`);
  }

  public isNavSectionActive(section: NavSection): boolean {
    return section.items.some(item => this.isNavItemActive(item.route));
  }

  public isNavSectionExpanded(section: NavSection): boolean {
    return this.expandedNavSectionId === section.id || this.isNavSectionActive(section) || this.navSearch.trim().length > 0;
  }

  public toggleNavSection(sectionId: string): void {
    this.expandedNavSectionId = this.expandedNavSectionId === sectionId ? null : sectionId;
  }
}

