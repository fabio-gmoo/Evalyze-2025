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
  ubicacion: string; // "Ciudad, País"
  salario?: string | null; // "45000 - 65000" | "A convenir" | null
  tipo_contrato?: string | null;
  activa: boolean;
  departamento?: string;
};

function parseUbicacion(ubicacion: string | undefined) {
  if (!ubicacion) return { city: '', country: '' };
  const [city, ...rest] = ubicacion.split(',');
  return { city: city?.trim() || '', country: rest.join(',').trim() || '' };
}
function parseSalario(s: string | null | undefined) {
  if (!s) return { salaryMin: undefined, salaryMax: undefined, currency: undefined };
  const match = s.match(/(\d+)\s*-\s*(\d+)/);
  if (!match) return { salaryMin: undefined, salaryMax: undefined, currency: undefined };
  return { salaryMin: Number(match[1]), salaryMax: Number(match[2]), currency: 'EUR' as const };
}
function composeSalario(min?: number, max?: number) {
  if (typeof min === 'number' && typeof max === 'number') return `${min} - ${max}`;
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
} {
  const { city, country } = parseUbicacion(v.ubicacion);
  const { salaryMin, salaryMax, currency } = parseSalario(v.salario ?? undefined);
  return {
    id: v.id,
    title: v.puesto,
    area: v.departamento ?? '',
    city,
    country,
    salaryMin,
    salaryMax,
    currency,
    candidatesCount: 0,
    aiDurationMin: 45,
    shortDescription: v.descripcion?.slice(0, 180),
    publishedAt: undefined,
    closesAt: undefined,
    status: v.activa ? 'active' : 'closed',
    descripcion: v.descripcion,
    requisitos: requisitosToArray(v.requisitos),
    tipo_contrato: v.tipo_contrato,
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
  const ubicacion =
    [payload.city, payload.country].filter(Boolean).join(', ') || payload.city || '';
  return {
    id: payload.id!,
    puesto: payload.title ?? '',
    descripcion: payload.descripcion ?? '',
    requisitos: requisitosToText(payload.requisitos),
    ubicacion,
    salario: composeSalario(payload.salaryMin, payload.salaryMax),
    tipo_contrato: payload.tipo_contrato ?? null,
    activa: payload.status ? payload.status === 'active' : true,
    departamento: payload.area ?? '',
  };
}

@Injectable({ providedIn: 'root' })
export class Vacancies {
  private http = inject(HttpClient);
  private base = `${environment.apiBase}/jobs`;

  listAll(): Observable<Vacancy[]> {
    return this.http.get<BackendVacante[]>(`${this.base}/`).pipe(map((arr) => arr.map(mapFromApi)));
  }

  /** Vacantes públicas activas (para postulante) */
  listActive(): Observable<Vacancy[]> {
    return this.listAll().pipe(map((list) => list.filter((v) => v.status === 'active')));
  }

  listMine(): Observable<Vacancy[]> {
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
    preguntas: any[];
  }> {
    // ¡Ojo! El endpoint correcto es "generate-ai" (con guion), igual al backend.
    return this.http.post<any>(`${this.base}/generate-ai/`, { puesto: title });
  }

  duplicate(id: number): Observable<Vacancy> {
    return this.http
      .post<BackendVacante>(`${this.base}/${id}/duplicate/`, {})
      .pipe(map(mapFromApi));
  }
}
