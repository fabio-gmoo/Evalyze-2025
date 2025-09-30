export type VacancyStatus = 'active' | 'closed';

export interface Vacancy {
  id: number;
  title: string;
  area: string; // p.ej. Tecnología / Datos
  city: string;
  country: string;
  salaryMin?: number;
  salaryMax?: number;
  currency?: string; // 'USD' | 'EUR' | ...
  candidatesCount?: number;
  aiDurationMin?: number;
  shortDescription?: string;
  publishedAt?: string; // ISO
  closesAt?: string; // ISO
  status: VacancyStatus;
}
