import { Vacancy } from '@interfaces/vacancy';
import { VacanteUI, FormData } from '@interfaces/vacante-model';

export function mapVacancyToUI(vacancy: Vacancy): VacanteUI {
  const salaryParts = [];
  if (vacancy.salaryMin) salaryParts.push(vacancy.salaryMin);
  if (vacancy.salaryMax) salaryParts.push(vacancy.salaryMax);
  const salario = salaryParts.length > 0 ? salaryParts.join(' - ') : undefined;

  return {
    id: vacancy.id,
    puesto: vacancy.title,
    departamento: vacancy.area || undefined,
    ubicacion: [vacancy.city, vacancy.country].filter(Boolean).join(', ') || 'No especificada',
    tipo_contrato: (vacancy as any).tipo_contrato || 'Tiempo Completo',
    salario: salario,
    descripcion: vacancy.shortDescription || (vacancy as any).descripcion || '',
    requisitos: (vacancy as any).requisitos || [],
    candidatos: (vacancy as any).candidatos || 0,
    activa: vacancy.status === 'active',
    company_name: vacancy.company_name, // NEW
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
