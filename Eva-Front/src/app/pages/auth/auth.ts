import { Component, signal, Input, inject, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID } from '@angular/core';

import { Login } from '@components/login/login';
import { Register } from '@components/register/register';

type Mode = 'login' | 'signup';
type Role = 'company' | 'candidate';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [Login, Register],
  templateUrl: './auth.html',
  styleUrl: './auth.scss',
})
export class Auth implements OnInit, OnDestroy {
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);

  mode = signal<Mode>('login');
  private timer: any;

  @Input() set startMode(value: Mode | undefined) {
    if (value) this.mode.set(value);
  }

  switchTo(next: Mode) { this.mode.set(next); }

  // ✅ Navegación centralizada aquí
  onLoginSuccess(role?: Role) {
    const stored =
      (typeof window !== 'undefined' && (sessionStorage.getItem('role') || localStorage.getItem('role'))) as Role | null;
    const finalRole: Role = role ?? stored ?? 'candidate';
    this.router.navigate(['/vacantes'], { queryParams: { mode: finalRole } });
  }

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const existingRole = this.getRoleFromStorage();
    if (this.hasToken() && existingRole) {
      this.navigateToVacantes(existingRole);
      return;
    }

    this.timer = setInterval(() => {
      if (this.hasToken()) {
        const r = this.getRoleFromStorage() ?? 'candidate';
        clearInterval(this.timer);
        this.navigateToVacantes(r);
      }
    }, 300);
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
  }

  private navigateToVacantes(role: Role) {
    if (!isPlatformBrowser(this.platformId)) return;
    this.router.navigate(['/vacantes'], { queryParams: { mode: role } });
  }

  private getRoleFromStorage(): Role | undefined {
    if (!isPlatformBrowser(this.platformId)) return undefined;
    try {
      const role =
        window.localStorage?.getItem('role') ||
        window.sessionStorage?.getItem('role') ||
        undefined;
      return (role as Role) || undefined;
    } catch { return undefined; }
  }

  private hasToken(): boolean {
    if (!isPlatformBrowser(this.platformId)) return false;
    try {
      if (window.localStorage?.getItem('token') || window.sessionStorage?.getItem('token')) return true;
      const cookie = typeof document !== 'undefined' ? (document.cookie || '') : '';
      return /\b(token|sid|session|auth)=/.test(cookie);
    } catch { return false; }
  }
}
