// src/app/pages/vacantes/vacantes.ts

import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';

import { Vacancies } from '@services/vacancies';
import { Vacancy } from '@interfaces/vacancy';

// Components
import { VacancyHeader } from '@components/vacancy-header/vacancy-header';
import { StatsGrid } from '@components/stats-grid/stats-grid';
import { VacancyTabs } from '@components/vacancy-tabs/vacancy-tabs';
import { VacancyList } from '@components/vacancy-list/vacancy-list';
import { VacancyModal } from '@components/vacancy-modal/vacancy-modal';
import { ChatDrawer } from '@components/chat-drawer/chat-drawer';

// Models
import {
  VacanteUI,
  ViewMode,
  StatCard,
  Pregunta,
  FormData,
  ChatMessage,
  Tab,
} from '@interfaces/vacante-model';

// Utils
import { mapVacancyToUI, getInitialFormData, getCurrentTime } from '@interfaces/vacancy-utils';

@Component({
  selector: 'app-vacantes',
  standalone: true,
  imports: [
    CommonModule,
    VacancyHeader,
    StatsGrid,
    VacancyTabs,
    VacancyList,
    VacancyModal,
    ChatDrawer,
  ],
  templateUrl: './vacantes.html',
  styleUrls: ['./vacantes.scss'],
})
export class Vacantes implements OnInit {
  private vacanciesService = inject(Vacancies);

  /** ====== State ====== */
  activeTab = signal<string>('vacantes');
  showModal = signal<boolean>(false);
  editingVacante = signal<VacanteUI | null>(null);
  loading = signal<boolean>(false);

  private initialMode(): ViewMode {
    const mode = new URLSearchParams(window.location.search).get('mode');
    return mode === 'candidate' ? 'candidate' : 'company';
  }
  viewMode = signal<ViewMode>(this.initialMode());

  preguntas = signal<Pregunta[]>([
    { id: 1, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' },
  ]);

  formData = signal<FormData>(getInitialFormData());

  stats = signal<StatCard[]>([
    { title: 'Vacantes Activas', value: 0, change: '+0 esta semana', color: 'blue' },
    { title: 'Candidatos', value: 0, change: '+0 hoy', color: 'green' },
    { title: 'Entrevistas IA', value: 0, change: '0 pendientes', color: 'purple' },
    { title: 'Contrataciones', value: 0, change: 'Este mes', color: 'yellow' },
  ]);

  tabs: Tab[] = [
    { id: 'vacantes', label: 'Vacantes' },
    { id: 'postulaciones', label: 'Postulaciones' },
    { id: 'entrevistas', label: 'Entrevistas IA' },
    { id: 'ranking', label: 'Ranking' },
    { id: 'informes', label: 'Informes' },
  ];

  vacantes = signal<VacanteUI[]>([]);

  /** ===== Chat (postulante) ===== */
  chatOpen = signal<boolean>(false);
  chatMessages = signal<ChatMessage[]>([]);
  chatVacante = signal<VacanteUI | null>(null);
  chatDraft = signal<string>('');

  /** ====== Lifecycle ====== */
  ngOnInit(): void {
    this.loadVacantes();
    if (this.viewMode() === 'company') this.loadStats();
  }

  /** ====== Data fetch ====== */
  loadVacantes(): void {
    this.loading.set(true);

    const obs =
      this.viewMode() === 'company'
        ? this.vacanciesService.listMine()
        : this.vacanciesService.listActive();

    obs.subscribe({
      next: (data: Vacancy[]) => {
        const mapped: VacanteUI[] = data.map(mapVacancyToUI);
        this.vacantes.set(mapped);
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        console.error('Error cargando vacantes:', error);
        this.loading.set(false);
      },
    });
  }

  loadStats(): void {
    this.vacanciesService.stats().subscribe({
      next: (data: { active: number; candidates: number; interviews: number; hires: number }) => {
        this.stats.set([
          {
            title: 'Vacantes Activas',
            value: data.active,
            change: '+2 esta semana',
            color: 'blue',
          },
          { title: 'Candidatos', value: data.candidates, change: '+18 hoy', color: 'green' },
          {
            title: 'Entrevistas IA',
            value: data.interviews,
            change: '15 pendientes',
            color: 'purple',
          },
          { title: 'Contrataciones', value: data.hires, change: 'Este mes', color: 'yellow' },
        ]);
      },
      error: (error: HttpErrorResponse) => {
        console.error('Error cargando estadísticas:', error);
      },
    });
  }

  /** ====== UI helpers ====== */
  setActiveTab(tabId: string): void {
    this.activeTab.set(tabId);
  }

  openModal(v: VacanteUI | null = null): void {
    if (v?.id) {
      this.vacanciesService.getById(v.id).subscribe({
        next: (full: Vacancy) => {
          this.editingVacante.set(v);
          this.formData.set({
            puesto: full.title,
            departamento: full.area || '',
            ubicacion: [full.city, full.country].filter(Boolean).join(', '),
            tipo_contrato: (full as any).tipo_contrato || 'Tiempo Completo',
            salarioMin: full.salaryMin?.toString() ?? '',
            salarioMax: full.salaryMax?.toString() ?? '',
            descripcion: (full as any).descripcion ?? full.shortDescription ?? '',
            requisitos: (full as any).requisitos ?? [''],
            duracion: 45,
            puntuacionMinima: 75,
          });
          this.showModal.set(true);
        },
        error: (_error: HttpErrorResponse) => {
          this.editingVacante.set(v);
          const [min, max] = (v.salario || '').split('-').map((s: string) => s?.trim());
          this.formData.set({
            puesto: v.puesto,
            departamento: v.departamento || '',
            ubicacion: v.ubicacion,
            tipo_contrato: v.tipo_contrato || 'Tiempo Completo',
            salarioMin: min || '',
            salarioMax: max || '',
            descripcion: v.descripcion || '',
            requisitos: v.requisitos?.length ? v.requisitos : [''],
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

  resetForm(): void {
    this.formData.set(getInitialFormData());
    this.preguntas.set([{ id: 1, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' }]);
  }

  updateFormField(event: { field: keyof FormData; value: string | number }): void {
    const current = this.formData();
    this.formData.set({ ...current, [event.field]: event.value as never });
  }

  updateArrayItem(event: { index: number; value: string }): void {
    const current = this.formData();
    const newArray = [...current.requisitos];
    newArray[event.index] = event.value;
    this.formData.set({ ...current, requisitos: newArray });
  }

  addArrayItem(): void {
    const current = this.formData();
    this.formData.set({ ...current, requisitos: [...current.requisitos, ''] });
  }

  removeArrayItem(index: number): void {
    const current = this.formData();
    if (current.requisitos.length > 1) {
      const newArray = current.requisitos.filter((_, i) => i !== index);
      this.formData.set({ ...current, requisitos: newArray });
    }
  }

  generarConIA(): void {
    const form = this.formData();
    if (!form.puesto.trim()) {
      alert('Por favor ingresa el título del puesto primero');
      return;
    }
    this.loading.set(true);
    this.vacanciesService.generateWithAI(form.puesto).subscribe({
      next: (response: {
        descripcion: string;
        requisitos: string[];
        preguntas: Array<{
          pregunta: string;
          tipo: string;
          peso?: number;
          palabras_clave?: string[];
        }>;
      }) => {
        const current = this.formData();
        this.formData.set({
          ...current,
          descripcion: response.descripcion,
          requisitos: response.requisitos,
        });

        if (response.preguntas?.length) {
          this.preguntas.set(
            response.preguntas.map((p, index) => ({
              id: index + 1,
              pregunta: p.pregunta,
              tipo: p.tipo,
              peso: p.peso ?? 20,
              palabrasClave: Array.isArray(p.palabras_clave) ? p.palabras_clave.join(', ') : '',
            })),
          );
        }
        this.loading.set(false);
        alert('Contenido generado con IA exitosamente');
      },
      error: (error: HttpErrorResponse) => {
        console.error('Error generando con IA:', error);
        this.loading.set(false);

        let msg = 'Error al generar contenido con IA';
        if (error.error) {
          if (typeof error.error === 'object' && 'detail' in error.error) {
            msg = (error.error as any).detail;
          } else if (typeof error.error === 'string') {
            msg = error.error;
          }
        }

        alert(msg);
      },
    });
  }

  guardarVacante(): void {
    const form = this.formData();
    const editing = this.editingVacante();

    if (!form.puesto.trim()) {
      alert('El título del puesto es requerido');
      return;
    }
    if (!form.descripcion.trim()) {
      alert('La descripción es requerida');
      return;
    }

    const payload = {
      id: editing?.id,
      title: form.puesto,
      area: form.departamento,
      city: form.ubicacion,
      salaryMin: form.salarioMin ? Number(form.salarioMin) : undefined,
      salaryMax: form.salarioMax ? Number(form.salarioMax) : undefined,
      status: 'active' as const,
      descripcion: form.descripcion,
      requisitos: form.requisitos.filter((r: string) => r.trim() !== ''),
      tipo_contrato: form.tipo_contrato,
    };

    this.loading.set(true);

    const obs = editing?.id
      ? this.vacanciesService.update(editing.id!, payload)
      : this.vacanciesService.create(payload);

    obs.subscribe({
      next: () => {
        this.loadVacantes();
        this.closeModal();
        alert(editing?.id ? 'Vacante actualizada exitosamente' : 'Vacante creada exitosamente');
      },
      error: (error: HttpErrorResponse) => {
        console.error('Error guardando vacante:', error);
        this.loading.set(false);
        alert('Error al guardar la vacante');
      },
    });
  }

  eliminarVacante(id: number): void {
    if (confirm('¿Estás seguro de eliminar esta vacante?')) {
      this.vacanciesService.delete(id).subscribe({
        next: () => {
          this.loadVacantes();
          alert('Vacante eliminada exitosamente');
        },
        error: (error: HttpErrorResponse) => {
          console.error('Error eliminando vacante:', error);
          alert('Error al eliminar vacante');
        },
      });
    }
  }

  /** ====== Preguntas ====== */
  addPregunta(): void {
    const list = this.preguntas();
    const nextId = (list.at(-1)?.id ?? 0) + 1;
    this.preguntas.set([
      ...list,
      { id: nextId, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' },
    ]);
  }

  removePregunta(index: number): void {
    const list = this.preguntas();
    this.preguntas.set(list.filter((_, i) => i !== index));
  }

  updatePregunta(event: { index: number; patch: Partial<Pregunta> }): void {
    const updated = this.preguntas().map((q, i) =>
      i === event.index ? { ...q, ...event.patch } : q,
    );
    this.preguntas.set(updated);
  }

  /** ===== Chat (postulante) ===== */
  openChat(v: VacanteUI): void {
    this.chatVacante.set(v);
    this.chatMessages.set([
      {
        from: 'bot',
        text: `¡Hola! Bienvenido a tu entrevista para "${v.puesto}". Te haré 4 preguntas. ¿Listo para comenzar?`,
        time: getCurrentTime(),
      },
    ]);
    this.chatOpen.set(true);
  }

  closeChat(): void {
    this.chatOpen.set(false);
    this.chatVacante.set(null);
    this.chatMessages.set([]);
    this.chatDraft.set('');
  }

  sendMessage(msg: string): void {
    if (!msg.trim()) return;
    const now = getCurrentTime();
    this.chatMessages.set([...this.chatMessages(), { from: 'user', text: msg, time: now }]);
    this.chatDraft.set('');

    setTimeout(() => {
      const follow = `Gracias por la información. En breve te pediremos tu CV y coordinaremos una entrevista.`;
      this.chatMessages.set([
        ...this.chatMessages(),
        { from: 'bot', text: follow, time: getCurrentTime() },
      ]);
    }, 450);
  }

  updateChatDraft(value: string): void {
    this.chatDraft.set(value);
  }
}
