import { FormsModule } from '@angular/forms';

import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';

// ⬇️ IMPORTA TU SERVICIO (ruta correcta desde /paginas/panel/)
import { VacanteService, VacanteDTO } from '../../services/vacante';
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
  totalScore: number; // promedio
  totalQuestions: number;
  perQuestion: QuestionResult[];
}

@Component({
  selector: 'app-panel',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, FormsModule],
  templateUrl: './panel.html',
  styleUrls: ['./panel.scss'],
})
export class Panel {
  view: 'vacantes' | 'postulaciones' | 'entrevistas' | 'ranking' | 'informes' | 'ver-vacante' =
    'vacantes';
  subVacTab: 'detalles' | 'entrevista' | 'candidatos' = 'detalles';

  showForm = false;
  @ViewChild('formAnchor') formAnchor!: ElementRef<HTMLDivElement>;
  form: FormGroup;

  // ⬇️ estados de envío / feedback API
  enviando = false;
  apiOk: string | null = null;
  apiError: string | null = null;

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
        {
          texto: 'Explique el ciclo de vida en React',
          tipo: 'Técnica',
          peso: 20,
          keywords: 'ciclo, effect, render',
        },
        {
          texto: 'Cuéntame un reto en equipo',
          tipo: 'Conductual',
          peso: 15,
          keywords: 'equipo, conflicto',
        },
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
      responsabilidades: 'Modelos predictivos\nAnálisis de datos\nPresentación de insights',
      duracionMin: 60,
      puntajeMin: 75,
      preguntas: [
        {
          texto: '¿Cómo evalúas un modelo?',
          tipo: 'Técnica',
          peso: 20,
          keywords: 'métricas, overfit',
        },
      ],
      estado: 'Activa',
      candidatos: 18,
      publicada: '7/1/2024',
      cierra: '14/2/2024',
    },
  ];

  postulaciones = [
    {
      nombre: 'Ana García',
      estado: 'Pendiente',
      email: 'ana.garcia@email.com',
      tel: '+34 612 345 678',
      posicion: 'Desarrollador Frontend',
      experiencia: '3 años',
      fecha: '14/1/2024',
      tags: ['React', 'TypeScript', 'Tailwind CSS'],
      carta: 'Soy una desarrolladora apasionada con experiencia en React y TypeScript...',
    },
    {
      nombre: 'Carlos López',
      estado: 'En Revisión',
      email: 'carlos.lopez@email.com',
      tel: '+34 623 456 789',
      posicion: 'Data Scientist',
      experiencia: '5 años',
      fecha: '11/1/2024',
      tags: ['Python', 'Machine Learning', 'SQL'],
      carta: 'Mi experiencia en análisis de datos y machine learning me permite...',
    },
  ];

  entrevistasIA = [
    {
      nombre: 'Ana García',
      posicion: 'Desarrollador Frontend',
      estado: 'Pendiente',
      preguntas: '0/5' as string,
      puntaje: '',
    },
    {
      nombre: 'Carlos López',
      posicion: 'Data Scientist',
      estado: 'Completada',
      preguntas: '5/5',
      puntaje: '82/100',
      inicio: '15/1/2024, 10:00:00',
    },
  ];

  ranking: {
    nombre: string;
    badges: string[];
    posicion: string;
    fecha: string;
    barras: {
      general: number;
      tecnica: number;
      conductual: number;
      experiencia: number;
      habilidades: number;
    };
    fortalezas: string[];
    mejoras: string[];
  }[] = [
    {
      nombre: 'Ana García',
      badges: ['Evaluado', 'Altamente Recomendado'],
      posicion: 'Desarrollador Frontend',
      fecha: '14/1/2024',
      barras: { general: 88, tecnica: 92, conductual: 85, experiencia: 87, habilidades: 90 },
      fortalezas: ['Excelentes conocimientos en React', 'Buena comunicación', 'Proactiva'],
      mejoras: ['Poca experiencia en testing', 'Podría mejorar en TypeScript'],
    },
    {
      nombre: 'Carlos López',
      badges: ['Aceptado', 'Recomendado'],
      posicion: 'Data Scientist',
      fecha: '11/1/2024',
      barras: { general: 82, tecnica: 89, conductual: 78, experiencia: 85, habilidades: 76 },
      fortalezas: ['Sólidos conocimientos en ML', 'Experiencia con Python', 'Analítico'],
      mejoras: ['Comunicación podría mejorar', 'Menos experiencia en producción'],
    },
  ];

  informes: { nombre: string; compat: number; gen: string }[] = [
    { nombre: 'Ana García', compat: 88, gen: '15/1/2024' },
    { nombre: 'Carlos López', compat: 82, gen: '12/1/2024' },
  ];

  showInformeDet = false;

  /* --- Estado Entrevistas --- */
  activeInterview: ActiveInterview | null = null;
  completedView: CompletedInterviewView | null = null;
  answerText = '';
  inputMode: 'texto' | 'voz' = 'texto';
  activeItemRef: any = null;

  constructor(
    private fb: FormBuilder,
    private vacantesSvc: VacanteService
  ) {
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
  agregarPregunta() {
    this.preguntas.push(this.nuevaPregunta());
  }
  eliminarPregunta(i: number) {
    if (this.preguntas.length > 1) this.preguntas.removeAt(i);
  }

  /* ---------- crear vacante (POST al backend) --------- */
  crearVacante() {
    this.apiOk = this.apiError = null;

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.scrollToForm();
      return;
    }

    this.enviando = true;

    // Crear el DTO directamente en el método crearVacante
    const dto: VacanteDTO = {
      titulo: this.form.value.titulo?.trim() || '',
      departamento: this.form.value.departamento || '',
      ubicacion: this.form.value.ubicacion || '',
      contrato: this.form.value.contrato || 'Tiempo Completo',
      salarioMin: Number(this.form.value.salarioMin) || 0,
      salarioMax: Number(this.form.value.salarioMax) || 0,
      descripcion: this.form.value.descripcion || '',
      requisitos: this.form.value.requisitos || '',
      responsabilidades: this.form.value.responsabilidades || '',
      duracionMin: Number(this.form.value.duracionMin) || 45,
      puntajeMin: Number(this.form.value.puntajeMin) || 75,
      preguntas: (this.form.value.preguntas || []).map((p: any) => ({
        texto: p?.texto || '',
        tipo: p?.tipo || 'Técnica',
        peso: Number(p?.peso) || 20,
        keywords: p?.keywords || '',
      })),
    };

    // Ahora llamamos al servicio para crear la vacante
    this.vacantesSvc.createVacante(dto).subscribe({
      next: (resp: any) => {
        const nuevoId = resp?.id ?? Date.now();

        const nueva: Vacante = {
          id: nuevoId,
          titulo: dto.titulo,
          empresa: dto.departamento || '—',
          departamento: dto.departamento,
          ubicacion: dto.ubicacion,
          contrato: dto.contrato,
          salarioMin: dto.salarioMin || undefined,
          salarioMax: dto.salarioMax || undefined,
          descripcion: dto.descripcion,
          requisitos: dto.requisitos,
          responsabilidades: dto.responsabilidades,
          duracionMin: dto.duracionMin,
          puntajeMin: dto.puntajeMin,
          preguntas: dto.preguntas as any,
          estado: 'Activa',
          candidatos: 0,
          publicada: new Date().toLocaleDateString('es-ES'),
        };

        // Añadir la vacante creada a la lista
        this.vacantes = [nueva, ...this.vacantes];

        this.apiOk = 'Vacante creada exitosamente';
        this.enviando = false;

        // Resetear formulario
      },
      error: (e) => {
        this.apiError = e?.error?.detail || e?.message || 'No se pudo crear la vacante';
        this.enviando = false;
      },
    });
  }
  verDetalles(v: Vacante) {
    this.selectedVacante = v;
    this.subVacTab = 'detalles';
    this.view = 'ver-vacante';
  }

  /* ---------- ENTREVISTAS ---------- */
  startInterview(item: any) {
    this.activeItemRef = item;
    const qs: InterviewQuestion[] = [
      {
        text: '¿Puedes contarme sobre tu experiencia con React y qué proyectos has desarrollado?',
        type: 'technical',
      },
      {
        text: 'Describe una situación donde tuviste que resolver un problema técnico complejo. ¿Cómo lo abordaste?',
        type: 'technical',
      },
      {
        text: '¿Cómo manejarías una situación donde tienes que trabajar con tecnologías que no conoces bien?',
        type: 'behavioral',
      },
      {
        text: 'Explica la diferencia entre “var”, “let” y “const” en JavaScript.',
        type: 'technical',
      },
      { text: '¿Por qué estás interesado en esta posición y en nuestra empresa?', type: 'general' },
    ];
    this.completedView = null;
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

    const baseScores = [85, 78, 82, 92, 75];
    const perQuestion: QuestionResult[] = this.activeInterview.questions.map((q, idx) => ({
      question: q.text,
      answer: this.activeInterview?.answers[idx] || '',
      score: baseScores[idx] ?? 80,
    }));
    const totalScore = Math.round(
      perQuestion.reduce((a, b) => a + b.score, 0) / perQuestion.length
    );

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

  openResults(item: any) {
    this.completedView = {
      candidate: item.nombre,
      position: item.posicion,
      totalScore: 82,
      totalQuestions: 5,
      perQuestion: [
        {
          question:
            '¿Puedes contarme sobre tu experiencia con React y qué proyectos has desarrollado?',
          answer: 'Tengo 3 años de experiencia con React…',
          score: 85,
        },
        {
          question:
            'Describe una situación donde tuviste que resolver un problema técnico complejo. ¿Cómo lo abordaste?',
          answer: 'Una vez tuve que optimizar una aplicación…',
          score: 78,
        },
        {
          question:
            '¿Cómo manejarías una situación donde tienes que trabajar con tecnologías que no conoces bien?',
          answer: 'Dedico tiempo a estudiar documentación…',
          score: 82,
        },
        {
          question: 'Explica la diferencia entre “var”, “let” y “const” en JavaScript.',
          answer: 'var tiene function scope; let y const tienen block scope…',
          score: 92,
        },
        {
          question: '¿Por qué estás interesado en esta posición y en nuestra empresa?',
          answer: 'Me interesa la empresa por su cultura de innovación…',
          score: 75,
        },
      ],
    };
    this.activeInterview = null;
    this.view = 'entrevistas';
  }

  volverListaEntrevistas() {
    this.completedView = null;
  }

  /* ---------- INFORMES ---------- */
  viewInforme() {
    this.view = 'informes';
    this.showInformeDet = true;
  }
  donutGradient(ok: number, bad: number, add: number): string {
    const t = ok + bad + add;
    const p1 = (ok / t) * 100;
    const p2 = (bad / t) * 100;
    const s1 = p1.toFixed(2);
    const s2 = (p1 + p2).toFixed(2);
    return `conic-gradient(#22c55e 0 ${s1}%, #ef4444 ${s1}% ${s2}%, #06b6d4 ${s2}% 100%)`;
  }
}
