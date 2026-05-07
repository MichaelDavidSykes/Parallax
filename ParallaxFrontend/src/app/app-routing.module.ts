import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { AutomationsComponent } from './automations/automations.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { TradingComponent } from './trading/trading.component';

const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'trading', component: TradingComponent },
  { path: 'automations', component: AutomationsComponent },
  { path: '**', redirectTo: 'dashboard' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
