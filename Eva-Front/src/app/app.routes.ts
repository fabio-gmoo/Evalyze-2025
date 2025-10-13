import { Routes } from '@angular/router';
import { Home } from '@pages/home/home';
import { Auth } from '@pages/auth/auth';
import { authGuard } from './auth-guard';
import { Vacantes } from '@pages/vacantes/vacantes';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: '/home' },
  { path: 'home', component: Home },
  { path: 'auth', component: Auth },

  // Genérico (lee ?mode=company|candidate o rol almacenado)
  { path: 'vacantes', component: Vacantes, canActivate: [authGuard] },

  // Atajos con "data" para fijar el modo sin query param
  { path: 'empresa/vacantes', component: Vacantes, canActivate: [authGuard], data: { mode: 'company' } },
  { path: 'candidato/vacantes', component: Vacantes, canActivate: [authGuard], data: { mode: 'candidate' } },

  // { path: '**', redirectTo: '/home' }, // opcional
];
