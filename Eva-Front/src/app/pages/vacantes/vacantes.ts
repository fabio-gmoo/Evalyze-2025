import { Component, computed, effect, inject, signal } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { Vacancies } from '@services/vacancies';
import { Vacancy } from '@interfaces/vacancy';
import { TokenStorage } from '@services/token-storage';
import { HasRole } from '@shared/has-role';
import { VacancyCard } from '@widgets/vacancy-card/vacancy-card';
import { StatsStrip } from '@widgets/stats-strip/stats-strip';

@Component({
  selector: 'app-vacantes',
  imports: [HasRole, VacancyCard, StatsStrip, AsyncPipe, RouterLink],
  templateUrl: './vacantes.html',
  styleUrl: './vacantes.scss',
})
export class Vacantes {
  private api = inject(Vacancies);
  private router = inject(Router);
  public store = inject(TokenStorage);

  tab = signal<'todas' | 'mias'>('todas');
  loading = signal(false);
  error = signal<string | null>(null);
  list = signal<Vacancy[]>([]);
  stats = signal<{ active: number; candidates: number; interviews: number; hires: number }>({
    active: 0,
    candidates: 0,
    interviews: 0,
    hires: 0,
  });

  role = computed(() => this.store.me?.role ?? 'candidate');

  constructor() {
    this.fetchStats();
    this.fetchList();

    effect(() => {
      const r = this.role();
      const t = this.tab();
      if (r === 'candidate' && t === 'mias') {
        this.tab.set('todas');
      }
    });
  }

  setTab(t: 'todas' | 'mias') {
    this.tab.set(t);
    this.fetchList();
  }

  hasRole(role: string): boolean {
    return this.role() === role;
  }

  private fetchStats() {
    this.api.stats().subscribe({
      next: (s) => this.stats.set(s),
      error: () => void 0,
    });
  }

  private fetchList() {
    this.loading.set(true);
    this.error.set(null);

    const req =
      this.role() === 'company' && this.tab() === 'mias' ? this.api.listMine() : this.api.listAll();

    req.subscribe({
      next: (rows) => this.list.set(rows),
      error: (e) => this.error.set(e?.error?.detail ?? 'No se pudieron cargar las vacantes'),
      complete: () => this.loading.set(false),
    });
  }

  navigateToNew() {
    this.router.navigate(['/vacantes/nueva']);
  }
}
