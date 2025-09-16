import { Routes } from '@angular/router';
import { HolaMundo } from './paginas/hola-mundo/hola-mundo';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'hola-mundo' },
  { path: 'hola-mundo', component: HolaMundo },

  { path: 'comenzar', loadComponent: () =>
      import('./paginas/comenzar/comenzar').then(m => m.Comenzar) },

  { path: 'ver-demo', loadComponent: () =>
      import('./paginas/ver-demo/ver-demo').then(m => m.VerDemo) },

  { path: '**', redirectTo: 'hola-mundo' }
];
