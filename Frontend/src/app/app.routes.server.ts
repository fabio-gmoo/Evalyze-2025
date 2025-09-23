import { Routes } from '@angular/router';
import { HolaMundo } from './paginas/hola-mundo/hola-mundo';
import { Panel } from './paginas/panel/panel';

export const serverRoutes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'hola-mundo' },
  { path: 'hola-mundo', component: HolaMundo },
  { path: 'comenzar', loadComponent: () =>
      import('./paginas/comenzar/comenzar').then(m => m.Comenzar) },
  { path: 'ver-demo', loadComponent: () =>
      import('./paginas/ver-demo/ver-demo').then(m => m.VerDemo) },
  { path: 'panel', component: Panel },
  { path: '**', redirectTo: 'hola-mundo' }
];
