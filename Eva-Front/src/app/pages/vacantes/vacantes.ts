// src/app/pages/vacantes/vacantes.ts
import { Component, OnInit, inject, signal, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

// Ajusta el import al servicio según tu estructura:
import { Vacancies } from '../../services/vacancies';
// Si en algún momento mueves el servicio a core, cambia por:
// import { Vacancies } from '../../core/services/vacancies';

import { Vacancy } from '@interfaces/vacancy';

/** ====== Tipos locales ====== */
interface Pregunta {
  id: number;
  pregunta: string;
  tipo: string;
  peso: number;
  palabrasClave: string;
}

interface VacanteUI {
  id?: number;
  puesto: string;
  descripcion: string;
  requisitos: string[];
  ubicacion: string; // "Ciudad, País"
  salario: string; // "45000 - 65000" | "A convenir"
  tipo_contrato: string | null | undefined;
  activa: boolean;
  departamento?: string;
  candidatos?: number;
  duracionIA?: string;
  publicada?: string;
  cierra?: string;
  preguntasIA?: number;
}

interface FormData {
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

type ViewMode = 'company' | 'candidate';

@Component({
  selector: 'app-vacantes',
  standalone: true,
  imports: [CommonModule, FormsModule],
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

  /** Modo de vista por query param: ?mode=company|candidate (default company) */
  private initialMode(): ViewMode {
    const mode = new URLSearchParams(window.location.search).get('mode');
    return mode === 'candidate' ? 'candidate' : 'company';
  }
  viewMode = signal<ViewMode>(this.initialMode());

  preguntas = signal<Pregunta[]>([
    { id: 1, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' },
  ]);

  formData = signal<FormData>({
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

  stats = signal([
    { title: 'Vacantes Activas', value: 0, change: '+0 esta semana', color: 'blue' as const },
    { title: 'Candidatos', value: 0, change: '+0 hoy', color: 'green' as const },
    { title: 'Entrevistas IA', value: 0, change: '0 pendientes', color: 'purple' as const },
    { title: 'Contrataciones', value: 0, change: 'Este mes', color: 'yellow' as const },
  ]);

  tabs = [
    { id: 'vacantes', label: 'Vacantes' },
    { id: 'postulaciones', label: 'Postulaciones' },
    { id: 'entrevistas', label: 'Entrevistas IA' },
    { id: 'ranking', label: 'Ranking' },
    { id: 'informes', label: 'Informes' },
  ] as const;

  vacantes = signal<VacanteUI[]>([]);

  /** ===== Chat (postulante) ===== */
  chatOpen = signal<boolean>(false);
  chatMessages = signal<{ from: 'user' | 'bot'; text: string; time: string }[]>([]);
  chatVacante = signal<VacanteUI | null>(null);
  chatDraft = '';
  @ViewChild('chatScroll') chatScroll?: ElementRef<HTMLDivElement>;

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
        const mapped: VacanteUI[] = data.map((v: Vacancy): VacanteUI => {
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
        });
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
            responsabilidades: [
              'Desarrollar interfaces de usuario',
              'Colaborar con el equipo de diseño',
            ],
            duracion: 45,
            puntuacionMinima: 75,
          });
          this.showModal.set(true);
        },
        error: (_error: HttpErrorResponse) => {
          // fallback con la card
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
            responsabilidades: [
              'Desarrollar interfaces de usuario',
              'Colaborar con el equipo de diseño',
            ],
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
    this.preguntas.set([{ id: 1, pregunta: '', tipo: 'Técnica', peso: 20, palabrasClave: '' }]);
  }

  updateFormField(field: keyof FormData, value: string | number): void {
    const current = this.formData();
    this.formData.set({ ...current, [field]: value as never });
  }

  updateArrayItem(field: 'requisitos' | 'responsabilidades', index: number, value: string): void {
    const current = this.formData();
    const newArray = [...current[field]];
    newArray[index] = value;
    this.formData.set({ ...current, [field]: newArray });
  }

  addArrayItem(field: 'requisitos' | 'responsabilidades'): void {
    const current = this.formData();
    this.formData.set({ ...current, [field]: [...current[field], ''] });
  }

  removeArrayItem(field: 'requisitos' | 'responsabilidades', index: number): void {
    const current = this.formData();
    if (current[field].length > 1) {
      const newArray = current[field].filter((_, i) => i !== index);
      this.formData.set({ ...current, [field]: newArray });
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
        responsabilidades: string[];
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
          responsabilidades: response.responsabilidades,
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
        alert('Error al generar contenido con IA');
      },
    });
  }

  guardarVacante(): void {
    const form = this.formData();
    const editing = this.editingVacante();

    // Validar campos obligatorios
    if (!form.puesto.trim()) {
      alert('El título del puesto es requerido');
      return;
    }
    if (!form.descripcion.trim()) {
      alert('La descripción es requerida');
      return;
    }

    // Construir el payload para crear o actualizar
    const payload = {
      id: editing?.id, // Si existe, se actualiza, sino se crea
      title: form.puesto,
      area: form.departamento,
      place: form.ubicacion,
      salaryMin: form.salarioMin ? Number(form.salarioMin) : undefined,
      salaryMax: form.salarioMax ? Number(form.salarioMax) : undefined,
      status: 'active' as const, // Por defecto, la vacante está activa
      descripcion: form.descripcion,
      requisitos: form.requisitos.filter((r: string) => r.trim() !== ''),
      tipo_contrato: form.tipo_contrato,
    };

    this.loading.set(true);

    // Llamar al servicio dependiendo si estamos creando o actualizando
    const obs = editing?.id
      ? this.vacanciesService.update(editing.id!, payload) // Actualizar si hay ID
      : this.vacanciesService.create(payload); // Crear si no hay ID

    obs.subscribe({
      next: () => {
        this.loadVacantes(); // Recargar vacantes
        this.closeModal(); // Cerrar modal
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

  /** ====== Preguntas: helpers para el template ====== */
  trackByPregunta = (_: number, item: Pregunta) => item.id;

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

  updatePregunta(index: number, patch: Partial<Pregunta>): void {
    const updated = this.preguntas().map((q, i) => (i === index ? { ...q, ...patch } : q));
    this.preguntas.set(updated);
  }

  /** ===== Chat (postulante) ===== */
  openChat(v: VacanteUI): void {
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
  closeChat(): void {
    this.chatOpen.set(false);
    this.chatVacante.set(null);
    this.chatMessages.set([]);
    this.chatDraft = '';
  }
  sendMessage(ev: Event) {
    ev.preventDefault();
    const msg = (this.chatDraft || '').trim();
    if (!msg) return;
    const now = this.timeNow();
    this.chatMessages.set([...this.chatMessages(), { from: 'user', text: msg, time: now }]);
    this.chatDraft = '';
    setTimeout(() => {
      const follow = `Gracias por la información. En breve te pediremos tu CV y coordinaremos una entrevista.`;
      this.chatMessages.set([
        ...this.chatMessages(),
        { from: 'bot', text: follow, time: this.timeNow() },
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
