import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import {
  ReactiveFormsModule,
  FormBuilder,
  FormGroup,
  FormArray,
  Validators,
  FormsModule,
} from '@angular/forms';

type EstadoVacante = 'Activa' | 'Borrador';

interface Pregunta {
  texto: string;
  tipo: 'Técnica' | 'Conductual' | 'Cultural' | string;
  peso: number;
  keywords: string;
}

interface Vacante {
  id: number;
  titulo: string;
  empresa?: string;
  departamento?: string;
  ubicacion?: string;
  contrato: string;
  salarioMin?: number;
  salarioMax?: number;
  descripcion?: string;
  requisitos?: string;
  responsabilidades?: string;
  duracionMin?: number;
  puntajeMin?: number;
  preguntas: Pregunta[];
  estado: EstadoVacante;
  candidatos: number;
  publicada?: string;
  cierra?: string;
}

/* ---- ENTREVISTAS ---- */
interface InterviewQuestion {
  text: string;
  type: 'technical' | 'behavioral' | 'general' | string;
}
interface ActiveInterview {
  candidate: string;
  position: string;
  questions: InterviewQuestion[];
  index: number;
  answers: string[];
  total: number;
}
interface QuestionResult {
  question: string;
  answer: string;
  score: number; // 0..100
}
interface CompletedInterviewView {
  candidate: string;
  position: string;
  totalScore: number;         // promedio
  totalQuestions: number;
  perQuestion: QuestionResult[];
}

// New: tipos para ranking/informes usados en el template
interface Bars { experiencia: number; habilidades: number; }
interface RankingItem {
  nombre: string;
  compat: number;
  gen: string; // fecha generado
  barras: Bars;
  fortalezas: string[];
  mejoras: string[];
}
interface InformeItem {
  nombre: string;
  compat: number;
  gen: string;
  barras?: Bars;
  fortalezas?: string[];
  mejoras?: string[];
}

@Component({
  selector: 'app-panel',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, FormsModule],
  templateUrl: './panel.html',
  styleUrls: ['./panel.scss'],
})
export class Panel {
  view: 'vacantes' | 'postulaciones' | 'entrevistas' | 'ranking' | 'informes' | 'ver-vacante' = 'vacantes';
  subVacTab: 'detalles' | 'entrevista' | 'candidatos' = 'detalles';

  showForm = false;
  @ViewChild('formAnchor') formAnchor!: ElementRef<HTMLDivElement>;
  form: FormGroup;

  selectedVacante: Vacante | null = null;

  vacantes: Vacante[] = [
    {
      id: 2,
      titulo: 'Desarrollador Frontend Senior',
      empresa: 'Tecnología',
      departamento: 'Tecnología',
      ubicacion: 'Madrid, España',
      contrato: 'Tiempo Completo',
      salarioMin: 45000,
      salarioMax: 65000,
      descripcion:
        'Buscamos un desarrollador frontend senior con experiencia en React y TypeScript para unirse a nuestro equipo de desarrollo.',
      requisitos: '5+ años en React\nTypeScript avanzado\nTesting con Jest',
      responsabilidades:
        'Desarrollar interfaces de usuario\nColaborar con el equipo de diseño\nOptimizar rendimiento',
      duracionMin: 45,
      puntajeMin: 75,
      preguntas: [
        { texto: 'Explique el ciclo de vida en React', tipo: 'Técnica', peso: 20, keywords: 'ciclo, effect, render' },
        { texto: 'Cuéntame un reto en equipo', tipo: 'Conductual', peso: 15, keywords: 'equipo, conflicto' },
      ],
      estado: 'Activa',
      candidatos: 23,
      publicada: '9/1/2024',
      cierra: '9/2/2024',
    },
    {
      id: 1,
      titulo: 'Data Scientist',
      empresa: 'Datos',
      departamento: 'Datos',
      ubicacion: 'Barcelona, España',
      contrato: 'Tiempo Completo',
      salarioMin: 50000,
      salarioMax: 70000,
      descripcion:
        'Científico de datos para análisis predictivo y machine learning en el sector fintech.',
      requisitos: 'Python\nMachine Learning\nSQL',
      responsabilidades:
        'Modelos predictivos\nAnálisis de datos\nPresentación de insights',
      duracionMin: 60,
      puntajeMin: 75,
      preguntas: [
        { texto: '¿Cómo evalúas un modelo?', tipo: 'Técnica', peso: 20, keywords: 'métricas, overfit' },
      ],
      estado: 'Activa',
      candidatos: 18,
      publicada: '7/1/2024',
      cierra: '14/2/2024',
    },
  ];

  postulaciones = [
    { nombre: 'Ana García', estado: 'Pendiente', email: 'ana.garcia@email.com', tel: '+34 612 345 678', posicion: 'Desarrollador Frontend', experiencia: '3 años', fecha: '14/1/2024', tags: ['React','TypeScript','Tailwind CSS'], carta: 'Soy una desarrolladora apasionada con experiencia en React y TypeScript...' },
    { nombre: 'Carlos López', estado: 'En Revisión', email: 'carlos.lopez@email.com', tel: '+34 623 456 789', posicion: 'Data Scientist', experiencia: '5 años', fecha: '11/1/2024', tags: ['Python','Machine Learning','SQL'], carta: 'Mi experiencia en análisis de datos y machine learning me permite...' },
  ];

  entrevistasIA = [
    { nombre: 'Ana García',    posicion: 'Desarrollador Frontend', estado: 'Pendiente',   preguntas: '0/5' as string, puntaje: '' },
    { nombre: 'Carlos López',  posicion: 'Data Scientist',         estado: 'Completada', preguntas: '5/5',             puntaje: '82/100', inicio: '15/1/2024, 10:00:00' },
  ];

  ranking: RankingItem[] = [
    {
      nombre: 'Ana García',
      compat: 92,
      gen: '16/1/2024',
      barras: { experiencia: 80, habilidades: 70 },
      fortalezas: ['Trabajo en equipo', 'Aprendizaje rápido'],
      mejoras: ['Profundizar en testing'],
    },
    {
      nombre: 'Carlos López',
      compat: 85,
      gen: '15/1/2024',
      barras: { experiencia: 75, habilidades: 68 },
      fortalezas: ['Análisis de datos', 'Comunicación'],
      mejoras: ['Experiencia en frontend'],
    },
  ];

  informes: InformeItem[] = [
    {
      nombre: 'Ana García',
      compat: 92,
      gen: '16/1/2024',
      barras: { experiencia: 80, habilidades: 70 },
      fortalezas: ['Trabajo en equipo', 'Aprendizaje rápido'],
      mejoras: ['Profundizar en testing'],
    },
  ];

  showInformeDet = false;

  /* --- Estado Entrevistas --- */
  activeInterview: ActiveInterview | null = null;
  completedView: CompletedInterviewView | null = null;
  answerText = '';
  inputMode: 'texto' | 'voz' = 'texto';

  constructor(private fb: FormBuilder) {
    this.form = this.fb.group({
      titulo: ['', Validators.required],
      departamento: [''],
      ubicacion: [''],
      contrato: ['Tiempo Completo'],
      salarioMin: [''],
      salarioMax: [''],
      descripcion: [''],
      requisitos: [''],
      responsabilidades: [''],
      duracionMin: ['45'],
      puntajeMin: ['75'],
      preguntas: this.fb.array([this.nuevaPregunta()]),
    });
  }

  /* ---------- form --------- */
  get preguntas(): FormArray<FormGroup> {
    return this.form.get('preguntas') as FormArray<FormGroup>;
  }
  private nuevaPregunta(): FormGroup {
    return this.fb.group({
      texto: [''],
      tipo: ['Técnica'],
      peso: ['20'],
      keywords: [''],
    });
  }

  /* ---------- navegación --------- */
  go(view: Panel['view']) {
    this.view = view;
    if (view !== 'ver-vacante') this.selectedVacante = null;
    if (view !== 'informes') this.showInformeDet = false;
    if (view !== 'entrevistas') this.completedView = null;
  }

  toggleForm() {
    this.showForm = !this.showForm;
    if (this.showForm) setTimeout(() => this.scrollToForm(), 30);
  }
  private scrollToForm() {
    if (typeof window !== 'undefined' && this.formAnchor) {
      this.formAnchor.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
  agregarPregunta() { this.preguntas.push(this.nuevaPregunta()); }
  eliminarPregunta(i: number) { if (this.preguntas.length > 1) this.preguntas.removeAt(i); }

  /* ---------- crear vacante --------- */
  crearVacante() {
    if (this.form.invalid) {
      this.form.markAllAsTouched(); this.scrollToForm(); return;
    }
    const v: Vacante = {
      id: Date.now(),
      titulo: this.form.value.titulo?.trim() || 'Nueva vacante',
      empresa: this.form.value.departamento || '—',
      departamento: this.form.value.departamento,
      ubicacion: this.form.value.ubicacion,
      contrato: this.form.value.contrato || 'Tiempo Completo',
      salarioMin: Number(this.form.value.salarioMin) || undefined,
      salarioMax: Number(this.form.value.salarioMax) || undefined,
      descripcion: this.form.value.descripcion,
      requisitos: this.form.value.requisitos,
      responsabilidades: this.form.value.responsabilidades,
      duracionMin: Number(this.form.value.duracionMin) || 45,
      puntajeMin: Number(this.form.value.puntajeMin) || 75,
      preguntas: (this.form.value.preguntas || []).map((p: any) => ({
        texto: p.texto || '', tipo: p.tipo || 'Técnica', peso: Number(p.peso) || 20, keywords: p.keywords || '',
      })),
      estado: 'Borrador',
      candidatos: 0,
      publicada: new Date().toLocaleDateString('es-ES'),
    };
    this.vacantes = [v, ...this.vacantes];
    this.form.reset({ contrato: 'Tiempo Completo', duracionMin: '45', puntajeMin: '75' });
    this.preguntas.clear(); this.preguntas.push(this.nuevaPregunta());
    this.showForm = false; this.view = 'vacantes';
    setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 50);
  }

  verDetalles(v: Vacante) {
    this.selectedVacante = v;
    this.subVacTab = 'detalles';
    this.view = 'ver-vacante';
  }

  /* ---------- ENTREVISTAS ---------- */
  startInterview(item: any) {
    const qs: InterviewQuestion[] = [
      { text: '¿Puedes contarme sobre tu experiencia con React y qué proyectos has desarrollado?', type: 'technical' },
      { text: 'Describe una situación donde tuviste que resolver un problema técnico complejo. ¿Cómo lo abordaste?', type: 'technical' },
      { text: '¿Cómo manejarías una situación donde tienes que trabajar con tecnologías que no conoces bien?', type: 'behavioral' },
      { text: 'Explica la diferencia entre “var”, “let” y “const” en JavaScript.', type: 'technical' },
      { text: '¿Por qué estás interesado en esta posición y en nuestra empresa?', type: 'general' },
    ];
    this.completedView = null; // limpio vista resumen
    this.activeInterview = {
      candidate: item.nombre,
      position: item.posicion,
      questions: qs,
      index: 0,
      answers: [],
      total: qs.length,
    };
    item.estado = 'En Progreso';
    item.preguntas = `1/${qs.length}`;
    this.answerText = '';
    this.inputMode = 'texto';
    this.view = 'entrevistas';
  }

  get interviewProgress(): number {
    if (!this.activeInterview) return 0;
    return (this.activeInterview.index / this.activeInterview.total) * 100;
  }

  nextQuestion(item: any) {
    if (!this.activeInterview) return;
    this.activeInterview.answers[this.activeInterview.index] = this.answerText || '';
    this.answerText = '';

    this.activeInterview.index++;
    if (this.activeInterview.index < this.activeInterview.total) {
      item.preguntas = `${this.activeInterview.index + 1}/${this.activeInterview.total}`;
      return;
    }

    // Finalizó: construir resumen (como la captura)
    const baseScores = [85, 78, 82, 92, 75];
    const perQuestion: QuestionResult[] = this.activeInterview.questions.map((q, idx) => ({
      question: q.text,
      answer: this.activeInterview?.answers[idx] || '',
      score: baseScores[idx] ?? 80,
    }));
    const totalScore = Math.round(perQuestion.reduce((a, b) => a + b.score, 0) / perQuestion.length);

    this.completedView = {
      candidate: item.nombre,
      position: item.posicion,
      totalScore,
      totalQuestions: perQuestion.length,
      perQuestion,
    };

    item.estado = 'Completada';
    item.preguntas = `${perQuestion.length}/${perQuestion.length}`;
    item.puntaje = `${totalScore}/100`;
    this.activeInterview = null;
    this.view = 'entrevistas';
  }

  /* abrir resumen para una entrevista ya completada desde el listado */
  openResults(item: any) {
    this.completedView = {
      candidate: item.nombre,
      position: item.posicion,
      totalScore: 82,
      totalQuestions: 5,
      perQuestion: [
        { question: '¿Puedes contarme sobre tu experiencia con React y qué proyectos has desarrollado?', answer: 'Tengo 3 años de experiencia con React…', score: 85 },
        { question: 'Describe una situación donde tuviste que resolver un problema técnico complejo. ¿Cómo lo abordaste?', answer: 'Una vez tuve que optimizar una aplicación…', score: 78 },
        { question: '¿Cómo manejarías una situación donde tienes que trabajar con tecnologías que no conoces bien?', answer: 'Dedico tiempo a estudiar documentación…', score: 82 },
        { question: 'Explica la diferencia entre “var”, “let” y “const” en JavaScript.', answer: 'var tiene function scope; let y const tienen block scope…', score: 92 },
        { question: '¿Por qué estás interesado en esta posición y en nuestra empresa?', answer: 'Me interesa la empresa por su cultura de innovación…', score: 75 },
      ],
    };
    this.activeInterview = null;
    this.view = 'entrevistas';
  }

  volverListaEntrevistas() { this.completedView = null; }

  /* ---------- INFORMES (se mantiene por si lo usas) ---------- */
  viewInforme() { this.view = 'informes'; this.showInformeDet = true; }
  donutGradient(ok: number, bad: number, add: number): string {
    const t = ok + bad + add;
    const p1 = (ok / t) * 100;
    const p2 = (bad / t) * 100;
    const s1 = p1.toFixed(2);
    const s2 = (p1 + p2).toFixed(2);
    return `conic-gradient(#22c55e 0 ${s1}%, #ef4444 ${s1}% ${s2}%, #06b6d4 ${s2}% 100%)`;
  }
}
