import { Routes } from '@angular/router';
import { Home } from '@/pages/home/home';
import { Auth } from '@/pages/auth/auth';

export const routes: Routes = [
  { path: 'home', component: Home },
  { path: '', pathMatch: 'full', redirectTo: '/home' },
  { path: 'auth', component: Auth },
];
