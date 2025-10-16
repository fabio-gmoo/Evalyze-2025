import { Vacancy } from '@interfaces/vacancy';
import { VacanteUI, FormData } from '@interfaces/vacante-model';

export function mapVacancyToUI(v: Vacancy): VacanteUI {
  const ubicacion = [v.city, v.country].filter(Boolean).join(', ');
  const salario =
    typeof v.salaryMin === 'number' && typeof v.salaryMax === 'number'
      ? `${v.salaryMin} - ${v.salaryMax}`
      : 'A convenir';

  return {
    id: v.id,
    puesto: v.title,
    descripcion: v.shortDescription || (v as any).descripcion || '',
    requisitos: (v as any).requisitos || [],
    ubicacion,
    salario,
    tipo_contrato: (v as any).tipo_contrato ?? null,
    activa: v.status === 'active',
    departamento: v.area || '',
    candidatos: v.candidatesCount ?? 0,
    duracionIA: (v.aiDurationMin ? `${v.aiDurationMin}min` : '45min') + ' IA',
    publicada: v.publishedAt
      ? new Date(v.publishedAt).toLocaleDateString('es-ES')
      : new Date().toLocaleDateString('es-ES'),
    cierra: v.closesAt
      ? new Date(v.closesAt).toLocaleDateString('es-ES')
      : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString('es-ES'),
    preguntasIA: 2,
  };
}

export function getInitialFormData(): FormData {
  return {
    puesto: '',
    departamento: '',
    ubicacion: '',
    tipo_contrato: 'Tiempo Completo',
    salarioMin: '',
    salarioMax: '',
    descripcion: '',
    requisitos: [''],

    duracion: 45,
    puntuacionMinima: 75,
  };
}

export function getCurrentTime(): string {
  return new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}
