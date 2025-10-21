// src/app/interfaces/vacancy.ts
export type VacancyStatus = 'active' | 'closed';

export interface CreatorInfo {
  id: number;
  email: string;
  name: string;
  role: 'company' | 'candidate';
}

export interface Vacancy {
  id: number;
  title: string;
  area: string;
  city: string;
  country: string;
  salaryMin?: number;
  salaryMax?: number;
  currency?: string;
  candidatesCount?: number;
  aiDurationMin?: number;
  shortDescription?: string;
  company_name?: string;
  updatedAt?: string;
  createdAt?: string;
  status: VacancyStatus;
  created_by_info?: CreatorInfo; // NEW
  applications_count?: number; // NEW
}

export interface Pregunta {
  id: number;
  pregunta: string;
  tipo: string;
  peso: number;
  palabrasClave: string;
}

export interface FormData {
  puesto: string;
  departamento: string;
  ubicacion: string;
  tipo_contrato: string;
  salarioMin: string;
  salarioMax: string;
  descripcion: string;
  requisitos: string[];
  responsabilidades: string[];
  duracion: number;
  puntuacionMinima: number;
}

export type ViewMode = 'company' | 'candidate';

export interface StatCard {
  title: string;
  value: number;
  change: string;
  color: 'blue' | 'green' | 'purple' | 'yellow';
}

export interface ChatMessage {
  from: 'user' | 'bot';
  text: string;
  time: string;
}

export interface Tab {
  id: string;
  label: string;
}
