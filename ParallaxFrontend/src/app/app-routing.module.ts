import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { BacktestsComponent } from './backtests/backtests.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { IntegrationsComponent } from './integrations/integrations.component';
import { MarketsComponent } from './markets/markets.component';
import { OpportunitiesComponent } from './opportunities/opportunities.component';
import { SimulatorComponent } from './simulator/simulator.component';

const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'markets', component: MarketsComponent },
  { path: 'opportunities', component: OpportunitiesComponent },
  { path: 'backtests', component: BacktestsComponent },
  { path: 'simulator', component: SimulatorComponent },
  { path: 'integrations', component: IntegrationsComponent },
  { path: '**', redirectTo: 'dashboard' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}

