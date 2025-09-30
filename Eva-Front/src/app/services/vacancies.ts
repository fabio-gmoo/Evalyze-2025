import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@environment';
import { Vacancy } from '@interfaces/vacancy';

@Injectable({
  providedIn: 'root',
})
export class Vacancies {
  private http = inject(HttpClient);
  private base = `${environment.apiBase}/jobs`;

  listAll(): Observable<Vacancy[]> {
    return this.http.get<Vacancy[]>(`${this.base}/`);
  }

  listMine(): Observable<Vacancy[]> {
    // endpoint sugerido en Django: /api/jobs/mine/
    return this.http.get<Vacancy[]>(`${this.base}/mine/`);
  }

  create(payload: Partial<Vacancy>): Observable<Vacancy> {
    return this.http.post<Vacancy>(`${this.base}/`, payload);
  }

  stats(): Observable<{ active: number; candidates: number; interviews: number; hires: number }> {
    // endpoint sugerido: /api/jobs/stats/  (puedes adaptarlo)
    return this.http.get<{ active: number; candidates: number; interviews: number; hires: number }>(
      `${this.base}/stats/`,
    );
  }
}
