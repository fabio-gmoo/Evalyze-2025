import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, delay, map } from 'rxjs/operators';
import { environment } from '@environment';

/** ===== Tipos compartidos ===== */
export type ApplicantStatus = 'Completada' | 'Programada' | 'En Revisión' | 'Pendiente';

export interface Vacancy {
  id: number;
  title: string;
  shortDescription?: string;
  descripcion?: string;
  requisitos?: string[];
  area?: string;
  city?: string;
  country?: string;
  salaryMin?: number;
  salaryMax?: number;
  status: 'active' | 'paused' | 'closed';
  candidatesCount?: number;
  aiDurationMin?: number;
  publishedAt?: string | Date;
  closesAt?: string | Date;
  tipo_contrato?: string;
  preguntasIA?: number;
}

export interface StatsDTO {
  active: number;
  candidates: number;
  interviews: number;
  hires: number;
}

export interface EntrevistaCfg {
  duracionMin: number;
  minimoAprobacion: number;
  preguntas: Array<{
    pregunta: string;
    tipo: string;
    peso: number;
    palabrasClave: string[];
  }>;
}

export interface Applicant {
  id: number;
  name: string;
  email: string;
  appliedAt: string;      // ISO string
  score: number;          // 0..100
  status: ApplicantStatus;
}

export interface RankingRow {
  name: string;
  skills: string[];
  entrevista: number;
  compatibilidad: number;
}

export interface ReportRow {
  name: string;
  score: number;
  strengths: string[];
  improvements: string[];
  recommendation: string;
}

/** ===== Tipos IA ===== */
export interface GenerateAIInput {
  title: string;                // puesto
  seniority?: string;           // junior / semi / senior...
  stack?: string[];             // ['React','TypeScript']
  area?: string;                // Tecnología / Datos...
  location?: string;            // "Madrid, España"
  contract?: string;            // Tiempo Completo...
  salaryMin?: number;
  salaryMax?: number;
  language?: 'es' | 'en';
}

export interface GenerateAIResponse {
  descripcion: string;
  requisitos: string[];
  responsabilidades: string[];
  preguntas: Array<{ pregunta: string; tipo: string; peso?: number; palabras_clave?: string[] }>;
}

@Injectable({ providedIn: 'root' })
export class Vacancies {
  constructor(private http: HttpClient) {}

  /**
   * Endpoint REAL del backend para IA.
   * En dev:  /api/jobs/generate-ai/  (via proxy)
   * En prod: https://evalyze-production.up.railway.app/jobs/generate-ai/
   */
  private AI_URL = `${environment.apiBase}/jobs/generate-ai/`;

  // =======================
  // Mocks de datos (se mantienen)
  // =======================
  private mockVacancies: Vacancy[] = [
    {
      id: 1,
      title: 'Desarrollador Frontend Senior',
      shortDescription: 'Buscamos un frontend senior con React y TypeScript.',
      requisitos: ['5+ años con React', 'TypeScript avanzado', 'Testing con Jest', 'Git y metodologías ágiles'],
      area: 'Tecnología',
      city: 'Madrid',
      country: 'España',
      salaryMin: 45000,
      salaryMax: 65000,
      status: 'active',
      candidatesCount: 23,
      aiDurationMin: 45,
      publishedAt: '2024-01-09',
      closesAt: '2024-02-09',
      tipo_contrato: 'Tiempo Completo',
      preguntasIA: 2,
    },
    {
      id: 2,
      title: 'Data Scientist',
      shortDescription: 'Analítica predictiva y ML en fintech.',
      requisitos: ['Python y R', 'Machine Learning', 'SQL avanzado', 'Modelos predictivos'],
      area: 'Datos',
      city: 'Barcelona',
      country: 'España',
      salaryMin: 50000,
      salaryMax: 70000,
      status: 'active',
      candidatesCount: 18,
      aiDurationMin: 60,
      publishedAt: '2024-01-07',
      closesAt: '2024-02-14',
      tipo_contrato: 'Tiempo Completo',
      preguntasIA: 1,
    },
  ];

  // =======================
  // Resumen/estadísticas
  // =======================
  stats(): Observable<StatsDTO> {
    const d: StatsDTO = {
      active: this.mockVacancies.filter(v => v.status === 'active').length,
      candidates: 247,
      interviews: 89,
      hires: 23,
    };
    return of(d).pipe(delay(120));
  }

  // =======================
  // Listados
  // =======================
  listMine(): Observable<Vacancy[]> {
    // “Empresa”: todas las vacantes creadas por la empresa (mock = todas)
    return of(this.mockVacancies).pipe(delay(120));
  }

  listActive(): Observable<Vacancy[]> {
    // “Candidato”: solo activas
    return of(this.mockVacancies.filter(v => v.status === 'active')).pipe(delay(120));
  }

  // =======================
  // CRUD básico (mock)
  // =======================
  getById(id: number): Observable<Vacancy> {
    const v = this.mockVacancies.find(x => x.id === id)!;
    return of(v).pipe(delay(80));
  }

  create(payload: Partial<Vacancy>): Observable<void> {
    const nextId = (this.mockVacancies.at(-1)?.id ?? 0) + 1;
    const v: Vacancy = {
      id: nextId,
      title: payload.title ?? 'Nuevo puesto',
      shortDescription: payload.shortDescription ?? payload.descripcion ?? '',
      requisitos: payload.requisitos ?? [],
      area: payload.area ?? '',
      city: payload.city ?? '',
      country: payload.country ?? '',
      salaryMin: payload.salaryMin,
      salaryMax: payload.salaryMax,
      status: (payload.status as any) ?? 'active',
      candidatesCount: 0,
      aiDurationMin: 45,
      publishedAt: new Date().toISOString(),
      closesAt: new Date(Date.now() + 30 * 86400000).toISOString(),
      tipo_contrato: payload.tipo_contrato ?? 'Tiempo Completo',
      preguntasIA: 1,
    };
    this.mockVacancies.push(v);
    return of(void 0).pipe(delay(120));
  }

  update(id: number, payload: Partial<Vacancy>): Observable<void> {
    const idx = this.mockVacancies.findIndex(x => x.id === id);
    if (idx >= 0) {
      this.mockVacancies[idx] = { ...this.mockVacancies[idx], ...payload };
    }
    return of(void 0).pipe(delay(120));
  }

  delete(id: number): Observable<void> {
    this.mockVacancies = this.mockVacancies.filter(v => v.id !== id);
    return of(void 0).pipe(delay(120));
  }

  // =======================
  // IA helpers / generación (BACKEND + fallback)
  // =======================
  /**
   * Llama al backend para generar descripción, requisitos, responsabilidades y preguntas.
   * Si el backend falla o no existe, devuelve un mock coherente.
   */
  generateWithAI(input: GenerateAIInput | string): Observable<GenerateAIResponse> {
    const title = typeof input === 'string' ? input : input.title;
    const body =
      typeof input === 'string'
        ? { puesto: title }
        : {
            // el backend mínimo espera "puesto"; el resto son opcionales
            puesto: input.title,
            seniority: input.seniority,
            stack: input.stack,
            area: input.area,
            location: input.location,
            contract: input.contract,
            salaryMin: input.salaryMin,
            salaryMax: input.salaryMax,
            language: input.language ?? 'es',
          };

    return this.http.post<any>(this.AI_URL, body).pipe(
      map((res: any) => {
        return {
          descripcion: res.descripcion ?? res.description ?? '',
          requisitos: res.requisitos ?? res.requirements ?? [],
          responsabilidades: res.responsabilidades ?? res.responsibilities ?? [],
          preguntas: (res.preguntas ?? res.questions ?? []).map((q: any) => ({
            pregunta: q.pregunta ?? q.text ?? '',
            tipo: q.tipo ?? q.type ?? 'técnica',
            peso: q.peso ?? q.weight ?? 20,
            palabras_clave: q.palabras_clave ?? q.keywords ?? [],
          })),
        } as GenerateAIResponse;
      }),
      catchError(() => {
        // === Fallback mock si el endpoint no responde ===
        const stackLine =
          typeof input !== 'string' && input.stack?.length ? ` con ${input.stack.join(', ')}` : '';
        const Senior = typeof input !== 'string' && input.seniority ? ` ${input.seniority}` : '';
        const desc =
          `Descripción generada por IA para el puesto "${title}${Senior}"${stackLine}. ` +
          `Esta posición se integra al área ${
            typeof input !== 'string' ? input.area ?? 'de Tecnología' : 'de Tecnología'
          }` +
          (typeof input !== 'string' && input.location ? ` en ${input.location}` : '') +
          `. Colaborarás con equipos cross para entregar features de alto impacto.`;

        const mock: GenerateAIResponse = {
          descripcion: desc,
          requisitos: [
            `Experiencia sólida en ${typeof input !== 'string' ? input.stack?.[0] ?? 'el stack requerido' : 'el stack requerido'}`,
            'Trabajo en equipo y buenas prácticas',
            'Comunicación efectiva',
            'Capacidad de aprendizaje continuo',
          ],
          responsabilidades: [
            'Diseñar e implementar nuevas funcionalidades',
            'Revisar código y proponer mejoras',
            'Optimizar performance y DX',
          ],
          preguntas: [
            { pregunta: 'Explica la diferencia entre estado y efecto en React.', tipo: 'técnica', peso: 25, palabras_clave: ['hooks','estado','efecto'] },
            { pregunta: '¿Cómo optimizarías una app React grande?', tipo: 'técnica', peso: 30, palabras_clave: ['memo','lazy','bundle splitting'] },
          ],
        };
        return of(mock).pipe(delay(250));
      })
    );
  }

  // =======================
  // Detalle: entrevista / postulantes / ranking / informes
  // =======================
  detailInterview(vacancyId: number): Observable<EntrevistaCfg> {
    const cfg: EntrevistaCfg = {
      duracionMin: 45,
      minimoAprobacion: 75,
      preguntas: [
        { pregunta: '¿Diferencia entre useState y useEffect?', tipo: 'técnica', peso: 25, palabrasClave: ['hooks', 'estado', 'efecto', 'renders'] },
        { pregunta: '¿Cómo optimizarías rendimiento en React?', tipo: 'técnica', peso: 30, palabrasClave: ['memo', 'useMemo', 'lazy', 'bundle splitting'] },
      ],
    };
    return of(cfg).pipe(delay(120));
  }

  detailApplicants(vacancyId: number): Observable<Applicant[]> {
    const rows: Applicant[] = [
      { id: 1, name: 'María González', email: 'maria.g@email.com', appliedAt: '2024-01-20', score: 85, status: 'Completada' },
      { id: 2, name: 'Carlos Ruiz', email: 'carlos.r@email.com', appliedAt: '2024-01-19', score: 78, status: 'En Revisión' },
      { id: 3, name: 'Ana López', email: 'ana.l@email.com', appliedAt: '2024-01-18', score: 72, status: 'Programada' },
    ];
    return of(rows).pipe(delay(160));
  }

  detailRanking(vacancyId: number): Observable<RankingRow[]> {
    const rows: RankingRow[] = [
      { name: 'María González', skills: ['React', 'TypeScript', 'Testing'], entrevista: 85, compatibilidad: 92 },
      { name: 'Carlos Ruiz', skills: ['React', 'JavaScript', 'Git'], entrevista: 78, compatibilidad: 85 },
      { name: 'Ana López', skills: ['Vue', 'JavaScript', 'CSS'], entrevista: 72, compatibilidad: 80 },
    ];
    return of(rows).pipe(delay(140));
  }

  detailReports(vacancyId: number): Observable<ReportRow[]> {
    const rows: ReportRow[] = [
      {
        name: 'María González',
        score: 85,
        strengths: ['Excelente conocimiento técnico', 'Buena comunicación', 'Experiencia relevante'],
        improvements: ['Poca experiencia en testing'],
        recommendation: 'Altamente recomendada para el puesto',
      },
      {
        name: 'Carlos Ruiz',
        score: 78,
        strengths: ['Sólidos fundamentos', 'Trabajo en equipo'],
        improvements: ['Mejorar TypeScript', 'Respuestas más detalladas'],
        recommendation: 'Recomendado con capacitación adicional',
      },
    ];
    return of(rows).pipe(delay(160));
  }
}
