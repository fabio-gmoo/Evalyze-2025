import { Routes } from '@angular/router';
import { Home } from '@pages/home/home';
import { Auth } from '@pages/auth/auth';
import { authGuard } from './auth-guard';
import { Vacantes } from '@pages/vacantes/vacantes';

export const routes: Routes = [
  { path: 'home', component: Home },
  { path: '', pathMatch: 'full', redirectTo: '/home' },
  { path: 'auth', component: Auth },
  { path: 'vacantes', component: Vacantes, canActivate: [authGuard] },
];
