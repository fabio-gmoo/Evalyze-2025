export interface Pregunta {
  id: number;
  pregunta: string;
  tipo: string;
  peso: number;
  palabrasClave: string;
}

export interface VacanteUI {
  id?: number;
  puesto: string;
  descripcion: string;
  requisitos: string[];
  ubicacion: string;
  salario: string;
  tipo_contrato: string | null | undefined;
  activa: boolean;
  departamento?: string;
  candidatos?: number;
  duracionIA?: string;
  publicada?: string;
  cierra?: string;
  preguntasIA?: number;
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
