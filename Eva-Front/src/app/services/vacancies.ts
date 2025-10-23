// src/app/core/services/vacancies.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@environment';
import { Vacancy } from '@interfaces/vacancy';
import { map } from 'rxjs/operators';

type BackendVacante = {
  id: number;
  puesto: string;
  descripcion: string;
  requisitos?: string | string[];
  ubicacion?: string;
  salario?: string | null;
  salariomin?: string | null;
  salariomax?: string | null;
  tipo_contrato?: string | null;
  activa: boolean;
  departamento?: string;
  company_name?: string;
  created_by_info?: {
    // NEW
    id: number;
    email: string;
    name: string;
    role: string;
  };
  applications_count?: number; // NEW
};
function parseUbicacion(ubicacion: string | undefined | null) {
  if (!ubicacion) return { city: '', country: '' };
  const [city, ...rest] = ubicacion.split(',');
  return { city: city?.trim() || '', country: rest.join(',').trim() || '' };
}

function parseSalarioFromApi(obj: BackendVacante) {
  // Si backend reporta separately, úsalos primero
  if (obj.salariomin || obj.salariomax) {
    const min = obj.salariomin ? Number(String(obj.salariomin).replace(/\D/g, '')) : undefined;
    const max = obj.salariomax ? Number(String(obj.salariomax).replace(/\D/g, '')) : undefined;
    return { salaryMin: min, salaryMax: max, currency: 'EUR' as const };
  }
  const s = obj.salario ?? undefined;
  if (!s) return { salaryMin: undefined, salaryMax: undefined, currency: undefined };
  const match = s.match(/(\d+)\s*-\s*(\d+)/);
  if (!match) return { salaryMin: undefined, salaryMax: undefined, currency: undefined };
  return { salaryMin: Number(match[1]), salaryMax: Number(match[2]), currency: 'EUR' as const };
}

function composeSalario(min?: number, max?: number) {
  if (typeof min === 'number' && typeof max === 'number') return `${min} - ${max}`;
  if (typeof min === 'number' && !max) return `${min}`;
  if (!min && typeof max === 'number') return `${max}`;
  return 'A convenir';
}

function requisitosToArray(requisitos: BackendVacante['requisitos']): string[] {
  if (!requisitos) return [];
  if (Array.isArray(requisitos)) return requisitos;
  return requisitos
    .split('\n')
    .map((r) => r.trim())
    .filter(Boolean);
}
function requisitosToText(arr?: string[]): string {
  return (arr ?? [])
    .map((r) => r.trim())
    .filter(Boolean)
    .join('\n');
}

function mapFromApi(v: BackendVacante): Vacancy & {
  descripcion: string;
  requisitos: string[];
  tipo_contrato?: string | null;
  created_by_info?: any;
  applications_count?: number;
} {
  const { city, country } = parseUbicacion(v.ubicacion ?? '');
  const { salaryMin, salaryMax, currency } = parseSalarioFromApi(v);

  return {
    id: v.id,
    title: v.puesto,
    area: v.departamento ?? '',
    city,
    country,
    salaryMin,
    salaryMax,
    currency,
    shortDescription: v.descripcion?.slice(0, 180),
    status: v.activa ? 'active' : 'closed',
    descripcion: v.descripcion,
    requisitos: requisitosToArray(v.requisitos),
    tipo_contrato: v.tipo_contrato,
    company_name: (v as any).company_name,
    created_by_info: (v as any).created_by_info, // NEW
    applications_count: (v as any).applications_count, // NEW
  };
}
/** ============ Mapper UI → API ============ */
function mapToApi(
  payload: Partial<Vacancy> & {
    descripcion?: string;
    requisitos?: string[];
    tipo_contrato?: string | null;
  },
): Partial<BackendVacante> {
  // El frontend a veces usa city como "Ciudad, País". Lo respetamos.
  const ubicacion =
    // preferir si el caller ya construyó la cadena
    (payload as any).ubicacion ||
    [payload.city, payload.country].filter(Boolean).join(', ') ||
    payload.city ||
    '';

  // Construimos el objeto base sin forzar `id` (evitamos id: undefined)
  const base: Partial<BackendVacante> = {
    puesto: payload.title ?? '',
    descripcion: payload.descripcion ?? '',
    requisitos: requisitosToText(payload.requisitos),
    ubicacion,
    salario: composeSalario(payload.salaryMin, payload.salaryMax),
    tipo_contrato: payload.tipo_contrato ?? null,
    activa: payload.status ? payload.status === 'active' : true,
    departamento: payload.area ?? '',
  };

  // Además, si vienen valores numericos separados, inclúyelos para compatibilidad con el backend
  if (typeof payload.salaryMin === 'number') base.salariomin = String(payload.salaryMin);
  if (typeof payload.salaryMax === 'number') base.salariomax = String(payload.salaryMax);

  if (typeof (payload as any).id === 'number') {
    (base as any).id = (payload as any).id;
  }

  return base;
}

@Injectable({ providedIn: 'root' })
export class Vacancies {
  private http = inject(HttpClient);
  private base = `${environment.apiBase}/jobs`;

  getAllVacancies(): Observable<Vacancy[]> {
    return this.http
      .get<BackendVacante[]>(`${this.base}/all-vacancies/`)
      .pipe(map((arr) => arr.map(mapFromApi)));
  }

  /** Vacantes públicas activas (para postulante) */
  listActive(): Observable<Vacancy[]> {
    return this.getAllVacancies().pipe(map((list) => list.filter((v) => v.status === 'active')));
  }

  getMine(): Observable<Vacancy[]> {
    return this.http
      .get<BackendVacante[]>(`${this.base}/mine/`)
      .pipe(map((arr) => arr.map(mapFromApi)));
  }

  getById(id: number): Observable<Vacancy> {
    return this.http.get<BackendVacante>(`${this.base}/${id}/`).pipe(map(mapFromApi));
  }

  create(
    payload: Partial<Vacancy> & {
      descripcion?: string;
      requisitos?: string[];
      tipo_contrato?: string | null;
      company_name?: string;
    },
  ): Observable<Vacancy> {
    const body = mapToApi(payload);
    return this.http.post<BackendVacante>(`${this.base}/`, body).pipe(map(mapFromApi));
  }

  update(
    id: number,
    payload: Partial<Vacancy> & {
      descripcion?: string;
      requisitos?: string[];
      tipo_contrato?: string | null;
    },
  ): Observable<Vacancy> {
    const body = mapToApi({ ...payload, id });
    return this.http.put<BackendVacante>(`${this.base}/${id}/`, body).pipe(map(mapFromApi));
  }

  patch(id: number, payload: Partial<Vacancy>): Observable<Vacancy> {
    const partial = mapToApi({ ...payload, id });
    return this.http.patch<BackendVacante>(`${this.base}/${id}/`, partial).pipe(map(mapFromApi));
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/${id}/`);
  }

  close(id: number): Observable<Vacancy> {
    return this.http
      .patch<BackendVacante>(`${this.base}/${id}/close/`, { activa: false })
      .pipe(map(mapFromApi));
  }

  reopen(id: number): Observable<Vacancy> {
    return this.http
      .patch<BackendVacante>(`${this.base}/${id}/reopen/`, { activa: true })
      .pipe(map(mapFromApi));
  }

  stats(): Observable<{ active: number; candidates: number; interviews: number; hires: number }> {
    return this.http.get<{ active: number; candidates: number; interviews: number; hires: number }>(
      `${this.base}/stats/`,
    );
  }

  generateWithAI(title: string): Observable<{
    descripcion: string;
    requisitos: string[];
    responsabilidades: string[];
  }> {
    // Endpoint: /jobs/generate-ai/
    return this.http.post<any>(`${this.base}/generate-ai/`, { puesto: title });
  }

  duplicate(id: number): Observable<Vacancy> {
    return this.http
      .post<BackendVacante>(`${this.base}/${id}/duplicate/`, {})
      .pipe(map(mapFromApi));
  }

  // save -> usa la acción custom en Django: /jobs/save/
  save(payload: Partial<Vacancy>): Observable<Vacancy> {
    const body = mapToApi(payload as any);
    return this.http.post<BackendVacante>(`${this.base}/save/`, body).pipe(map(mapFromApi));
  }

  apply(vacancyId: number): Observable<any> {
    return this.http.post(`${this.base}/${vacancyId}/apply/`, {});
  }

  getApplications(vacancyId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/${vacancyId}/applications/`);
  }

  getMyApplications(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/my-applications`);
  }
}
