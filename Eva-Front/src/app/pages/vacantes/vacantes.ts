// src/app/pages/vacantes/vacantes.ts
import { Component, OnInit, inject, signal, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';

import {
  Vacancies,
  Vacancy,
  StatsDTO,
  EntrevistaCfg,
  Applicant,
  RankingRow,
  ReportRow,
} from '../../services/vacancies';

type ViewMode = 'company' | 'candidate';
type MasterView = 'list' | 'detail';

interface VacanteUI {
  id?: number;
  puesto: string;
  descripcion: string;
  requisitos: string[];
  ubicacion: string;
  salario: string;
  tipo_contrato?: string | null;
  activa: boolean;
  departamento?: string;
  candidatos?: number;
  duracionIA?: string;
  publicada?: string;
  cierra?: string;
  preguntasIA?: number;
}

type PreguntaUI = { id: number; pregunta: string; tipo: string; peso: number; palabrasClave: string };

type FormModel = {
  puesto: string;
  departamento: string;
  ubicacion: string;
  tipo_contrato: string;
  salarioMin: string | number;
  salarioMax: string | number;
  descripcion: string;
  requisitos: string[];
  responsabilidades: string[];
  duracion: number;
  puntuacionMinima: number;
};

@Component({
  selector: 'app-vacantes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './vacantes.html',
  styleUrls: ['./vacantes.scss'],
})
export class Vacantes implements OnInit {
  /** Servicios / Router */
  private vacanciesService = inject(Vacancies);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  // pestañas que usa el HTML (empresa)
  tabs = [
    { id: 'vacantes', label: 'Vacantes' },
    { id: 'postulaciones', label: 'Postulaciones' },
    { id: 'entrevistas', label: 'Entrevistas IA' },
    { id: 'ranking', label: 'Ranking' },
    { id: 'informes', label: 'Informes' },
  ] as const;

  // para que el <h2> del modal sepa si es editar/crear
  editingVacante = signal<VacanteUI | null>(null);

  /** Estado principal */
  viewMode = signal<ViewMode>('company'); // se resuelve en ngOnInit()
  masterView = signal<MasterView>('list');
  activeTab = signal<string>('vacantes');
  detailActiveTab = signal<string>('detalles');
  showModal = signal<boolean>(false);
  loading = signal<boolean>(false);

  /** Listas / dashboard */
  vacantes = signal<VacanteUI[]>([]);
  stats = signal([
    { title: 'Vacantes Activas', value: 0, change: '+0 esta semana', color: 'blue' as const },
    { title: 'Candidatos', value: 0, change: '+0 hoy', color: 'green' as const },
    { title: 'Entrevistas IA', value: 0, change: '0 pendientes', color: 'purple' as const },
    { title: 'Contrataciones', value: 0, change: 'Este mes', color: 'yellow' as const },
  ]);

  /** Detalle */
  selectedVacancy = signal<VacanteUI | null>(null);
  detailInterview = signal<EntrevistaCfg | null>(null);
  detailApplicants = signal<Applicant[]>([]);
  detailRanking = signal<RankingRow[]>([]);
  detailReports = signal<ReportRow[]>([]);

  /** Form + preguntas IA */
  preguntas = signal<PreguntaUI[]>([
    { id: 1, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' },
  ]);

  formData = signal<FormModel>({
    puesto: '',
    departamento: '',
    ubicacion: '',
    tipo_contrato: 'Tiempo Completo',
    salarioMin: '',
    salarioMax: '',
    descripcion: '',
    requisitos: [''],
    responsabilidades: [''],
    duracion: 45,
    puntuacionMinima: 75,
  });

  /** Chat candidato (mock) */
  chatOpen = signal<boolean>(false);
  chatMessages = signal<{ from: 'user' | 'bot'; text: string; time: string }[]>([]);
  chatVacante = signal<VacanteUI | null>(null);
  chatDraft = '';
  @ViewChild('chatScroll') chatScroll?: ElementRef<HTMLDivElement>;

  // ========= lifecycle =========
  ngOnInit(): void {
    // Resolver modo al cargar (ruta data, query o rol guardado)
    this.viewMode.set(this.resolveMode());

    this.loadVacantes();
    if (this.viewMode() === 'company') this.loadStats();

    // Reaccionar a cambios de data en la ruta (/empresa/vacantes o /candidato/vacantes)
    this.route.data.subscribe((d) => {
      if (d?.['mode']) {
        const m = d['mode'] as ViewMode;
        if (m !== this.viewMode()) {
          this.viewMode.set(m);
          this.masterView.set('list');
          this.activeTab.set('vacantes');
          this.selectedVacancy.set(null);
          this.loadVacantes();
          if (m === 'company') this.loadStats();
        }
      }
    });

    // Reaccionar a cambios de query param (?mode=company|candidate)
    this.route.queryParamMap.subscribe((q) => {
      const m = q.get('mode');
      if (m === 'candidate' || m === 'company') {
        if (m !== this.viewMode()) {
          this.viewMode.set(m);
          this.masterView.set('list');
          this.activeTab.set('vacantes');
          this.selectedVacancy.set(null);
          this.loadVacantes();
          if (m === 'company') this.loadStats();
        }
      }
    });
  }

  /** Decide el modo con prioridad: data de la ruta > query param > rol guardado > company */
  private resolveMode(): ViewMode {
    const dataMode = this.route.snapshot.data?.['mode'];
    if (dataMode === 'candidate' || dataMode === 'company') return dataMode;

    const qp = this.route.snapshot.queryParamMap.get('mode');
    if (qp === 'candidate' || qp === 'company') return qp;

    const role = (localStorage.getItem('role') || sessionStorage.getItem('role') || '').toLowerCase();
    if (role.includes('candi')) return 'candidate';

    return 'company';
  }

  // ========= dashboard/listas =========
  setActiveTab(tabId: string) { this.activeTab.set(tabId); }

  loadStats() {
    this.vacanciesService.stats().subscribe({
      next: (d: StatsDTO) => {
        this.stats.set([
          { title: 'Vacantes Activas', value: d.active,      change: '+2 esta semana', color: 'blue' },
          { title: 'Candidatos',       value: d.candidates,  change: '+18 hoy',        color: 'green' },
          { title: 'Entrevistas IA',   value: d.interviews,  change: '15 pendientes',  color: 'purple' },
          { title: 'Contrataciones',   value: d.hires,       change: 'Este mes',       color: 'yellow' },
        ]);
      },
      error: (e: HttpErrorResponse) => console.error('stats()', e),
    });
  }

  loadVacantes() {
    this.loading.set(true);
    const obs = this.viewMode() === 'company'
      ? this.vacanciesService.listMine()
      : this.vacanciesService.listActive();

    obs.subscribe({
      next: (rows: Vacancy[]) => {
        const mapped: VacanteUI[] = rows.map((v: Vacancy) => ({
          id: v.id,
          puesto: v.title,
          descripcion: v.shortDescription ?? v.descripcion ?? '',
          requisitos: v.requisitos ?? [],
          ubicacion: [v.city, v.country].filter(Boolean).join(', '),
          salario:
            typeof v.salaryMin === 'number' && typeof v.salaryMax === 'number'
              ? `${v.salaryMin} - ${v.salaryMax}`
              : 'A convenir',
          tipo_contrato: v.tipo_contrato ?? 'Tiempo Completo',
          activa: v.status === 'active',
          departamento: v.area ?? 'Tecnología',
          candidatos: v.candidatesCount ?? 0,
          duracionIA: (v.aiDurationMin ? `${v.aiDurationMin}min` : '45min') + ' IA',
          publicada: v.publishedAt
            ? new Date(v.publishedAt).toLocaleDateString('es-ES')
            : new Date().toLocaleDateString('es-ES'),
          cierra: v.closesAt ? new Date(v.closesAt).toLocaleDateString('es-ES') : '',
          preguntasIA: v.preguntasIA ?? 1,
        }));
        this.vacantes.set(mapped);
        this.loading.set(false);
      },
      error: (e: HttpErrorResponse) => {
        console.error('loadVacantes()', e);
        this.loading.set(false);
      },
    });
  }

  // ========= detalle =========
  verDetalles(v: VacanteUI) {
    this.selectedVacancy.set(v);
    this.detailActiveTab.set('detalles');
    this.masterView.set('detail');

    this.vacanciesService.detailInterview(v.id!).subscribe((cfg: EntrevistaCfg) => this.detailInterview.set(cfg));
    this.vacanciesService.detailApplicants(v.id!).subscribe((rows: Applicant[]) => this.detailApplicants.set(rows));
    this.vacanciesService.detailRanking(v.id!).subscribe((rows: RankingRow[]) => this.detailRanking.set(rows));
    this.vacanciesService.detailReports(v.id!).subscribe((rows: ReportRow[]) => this.detailReports.set(rows));
  }

  volverALista() {
    this.masterView.set('list');
    this.detailActiveTab.set('detalles');
    this.selectedVacancy.set(null);
  }

  setDetailTab(tab: string) { this.detailActiveTab.set(tab); }

  // ========= modal crear/editar =========
  openModal(v: VacanteUI | null = null): void {
    if (v?.id) {
      this.editingVacante.set(v);
      this.vacanciesService.getById(v.id).subscribe({
        next: (full) => {
          this.formData.set({
            puesto: full.title ?? v.puesto,
            departamento: full.area ?? v.departamento ?? '',
            ubicacion: [full.city, full.country].filter(Boolean).join(', ') || v.ubicacion,
            tipo_contrato: full.tipo_contrato ?? v.tipo_contrato ?? 'Tiempo Completo',
            salarioMin: full.salaryMin?.toString() ?? (v.salario?.split('-')[0]?.trim() ?? ''),
            salarioMax: full.salaryMax?.toString() ?? (v.salario?.split('-')[1]?.trim() ?? ''),
            descripcion: full.descripcion ?? full.shortDescription ?? v.descripcion ?? '',
            requisitos: full.requisitos ?? v.requisitos ?? [''],
            responsabilidades: ['Desarrollar interfaces de usuario', 'Colaborar con el equipo de diseño'],
            duracion: 45,
            puntuacionMinima: 75,
          });
          this.showModal.set(true);
        },
        error: () => {
          // fallback mínimo
          this.formData.set({
            puesto: v.puesto,
            departamento: v.departamento ?? '',
            ubicacion: v.ubicacion,
            tipo_contrato: v.tipo_contrato ?? 'Tiempo Completo',
            salarioMin: v.salario?.split('-')[0]?.trim() ?? '',
            salarioMax: v.salario?.split('-')[1]?.trim() ?? '',
            descripcion: v.descripcion ?? '',
            requisitos: v.requisitos?.length ? v.requisitos : [''],
            responsabilidades: ['Desarrollar interfaces de usuario', 'Colaborar con el equipo de diseño'],
            duracion: 45,
            puntuacionMinima: 75,
          });
          this.showModal.set(true);
        },
      });
    } else {
      this.editingVacante.set(null);
      this.resetForm();
      this.showModal.set(true);
    }
  }

  closeModal(): void {
    this.showModal.set(false);
    this.editingVacante.set(null);
    this.resetForm();
  }

  /** Resetea el formulario y las preguntas del modal */
  private resetForm(): void {
    this.formData.set({
      puesto: '',
      departamento: '',
      ubicacion: '',
      tipo_contrato: 'Tiempo Completo',
      salarioMin: '',
      salarioMax: '',
      descripcion: '',
      requisitos: [''],
      responsabilidades: [''],
      duracion: 45,
      puntuacionMinima: 75,
    });
    this.preguntas.set([
      { id: 1, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' },
    ]);
  }

  updateFormField(field: keyof FormModel, value: string | number) {
    this.formData.set({ ...this.formData(), [field]: value } as FormModel);
  }
  updateArrayItem(field: 'requisitos' | 'responsabilidades', i: number, value: string) {
    const current = this.formData();
    const arr = [...current[field]];
    arr[i] = value;
    this.formData.set({ ...current, [field]: arr });
  }
  addArrayItem(field: 'requisitos' | 'responsabilidades') {
    const current = this.formData();
    this.formData.set({ ...current, [field]: [...current[field], ''] });
  }
  removeArrayItem(field: 'requisitos' | 'responsabilidades', i: number) {
    const current = this.formData();
    if (current[field].length > 1) {
      this.formData.set({ ...current, [field]: current[field].filter((_, idx) => idx !== i) });
    }
  }

  generarConIA(): void {
  const f = this.formData();
  if (!f.puesto.trim()) {
    alert('Por favor ingresa el título del puesto primero');
    return;
  }
  this.loading.set(true);

  const payload = {
    title: f.puesto,
    seniority: /senior/i.test(f.puesto) ? 'senior' : /junior/i.test(f.puesto) ? 'junior' : undefined,
    stack: this.formData().requisitos.filter(x => x && x.length <= 25), // heurística: usa requisitos cortos como stack
    area: f.departamento || 'Tecnología',
    location: f.ubicacion,
    contract: f.tipo_contrato,
    salaryMin: f.salarioMin ? Number(f.salarioMin) : undefined,
    salaryMax: f.salarioMax ? Number(f.salarioMax) : undefined,
    language: 'es' as const,
  };

  this.vacanciesService.generateWithAI(payload).subscribe({
    next: (res) => {
      // Descripción + listas
      this.formData.set({
        ...this.formData(),
        descripcion: res.descripcion || this.formData().descripcion,
        requisitos: res.requisitos?.length ? res.requisitos : this.formData().requisitos,
        responsabilidades: res.responsabilidades?.length ? res.responsabilidades : this.formData().responsabilidades,
      });

      // Preguntas IA → UI
      if (Array.isArray(res.preguntas) && res.preguntas.length) {
        this.preguntas.set(
          res.preguntas.map((p, idx) => ({
            id: idx + 1,
            pregunta: p.pregunta,
            tipo: p.tipo || 'Técnica',
            peso: p.peso ?? 20,
            palabrasClave: (p.palabras_clave ?? []).join(', '),
          }))
        );
      }

      this.loading.set(false);
      alert('Contenido generado con IA exitosamente');
    },
    error: (err) => {
      console.error('generateWithAI() error', err);
      this.loading.set(false);
      alert('Error al generar contenido con IA');
    }
  });
}

  guardarVacante() {
    const f = this.formData();
    if (!f.puesto.trim()) return alert('El título del puesto es requerido');
    if (!f.descripcion.trim()) return alert('La descripción es requerida');

    const payload: Partial<Vacancy> = {
      title: f.puesto,
      area: f.departamento,
      city: f.ubicacion.split(',')[0]?.trim(),
      country: f.ubicacion.split(',')[1]?.trim(),
      salaryMin: f.salarioMin ? Number(f.salarioMin) : undefined,
      salaryMax: f.salarioMax ? Number(f.salarioMax) : undefined,
      status: 'active',
      descripcion: f.descripcion,
      requisitos: f.requisitos.filter((x) => x.trim()),
      tipo_contrato: f.tipo_contrato,
    };

    this.loading.set(true);
    // Usa el id de edición si existe; si no, cae al seleccionado (detalle)
    const editingId = this.editingVacante()?.id ?? this.selectedVacancy()?.id;

    const req$ = editingId
      ? this.vacanciesService.update(editingId, payload)
      : this.vacanciesService.create(payload);

    req$.subscribe({
      next: () => {
        this.loading.set(false);
        this.closeModal();
        this.loadVacantes();
        alert('Vacante guardada');
      },
      error: () => {
        this.loading.set(false);
        alert('Error guardando la vacante');
      },
    });
  }

  eliminarVacante(id: number) {
    if (!confirm('¿Eliminar esta vacante?')) return;
    this.vacanciesService.delete(id).subscribe({
      next: () => {
        this.loadVacantes();
        if (this.selectedVacancy()?.id === id) this.volverALista();
        alert('Vacante eliminada');
      },
      error: () => alert('No se pudo eliminar'),
    });
  }

  // ========= preguntas (modal) =========
  trackByPregunta = (_: number, it: { id: number }) => it.id;
  addPregunta() {
    const list = this.preguntas();
    const nextId = (list.at(-1)?.id ?? 0) + 1;
    this.preguntas.set([...list, { id: nextId, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' }]);
  }
  removePregunta(i: number) {
    this.preguntas.set(this.preguntas().filter((_, idx) => idx !== i));
  }
  updatePregunta(
    i: number,
    patch: Partial<{ pregunta: string; tipo: string; peso: number; palabrasClave: string }>
  ) {
    this.preguntas.set(this.preguntas().map((q, idx) => (idx === i ? { ...q, ...patch } : q)));
  }

  // ========= chat (candidato) =========
  openChat(v: VacanteUI) {
    this.chatVacante.set(v);
    this.chatMessages.set([
      {
        from: 'bot',
        text: `¡Hola! Bienvenido a tu entrevista para “${v.puesto}”. Te haré 4 preguntas. ¿Listo para comenzar?`,
        time: this.timeNow(),
      },
    ]);
    this.chatOpen.set(true);
    setTimeout(() => this.scrollChatBottom(), 0);
  }
  closeChat() {
    this.chatOpen.set(false);
    this.chatVacante.set(null);
    this.chatMessages.set([]);
    this.chatDraft = '';
  }
  sendMessage(ev: Event) {
    ev.preventDefault();
    const msg = (this.chatDraft || '').trim();
    if (!msg) return;
    this.chatMessages.set([...this.chatMessages(), { from: 'user', text: msg, time: this.timeNow() }]);
    this.chatDraft = '';
    setTimeout(() => {
      this.chatMessages.set([
        ...this.chatMessages(),
        { from: 'bot', text: 'Gracias. En breve te pediremos tu CV y coordinaremos una entrevista.', time: this.timeNow() },
      ]);
      this.scrollChatBottom();
    }, 450);
    this.scrollChatBottom();
  }
  private timeNow(): string {
    return new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  }
  private scrollChatBottom() {
    try {
      this.chatScroll?.nativeElement.scrollTo({
        top: this.chatScroll.nativeElement.scrollHeight,
        behavior: 'smooth',
      });
    } catch {}
  }
}
