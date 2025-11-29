import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VacanteUI, Tab } from '@interfaces/vacante-model';
import { VacancyTabs } from '@components/vacancy-tabs/vacancy-tabs';
import { InterviewChat } from '@components/interview-chat/interview-chat';
import { Interview } from '@services/interview';
import { Vacancies } from '@services/vacancies';

@Component({
  selector: 'app-vacancy-details-modal',
  imports: [CommonModule, FormsModule, VacancyTabs, InterviewChat],
  templateUrl: './vacancy-details-modal.html',
  styleUrl: './vacancy-details-modal.scss',
})
export class VacancyDetailsModal implements OnInit {
  private interviewService = inject(Interview);
  private vacanciesService = inject(Vacancies);

  @Input() vacancy!: VacanteUI;
  @Input() viewMode: 'company' | 'candidate' = 'company';
  @Input() loading: boolean = false;

  @Output() close = new EventEmitter<void>();
  @Output() apply = new EventEmitter<VacanteUI>();
  @Output() edit = new EventEmitter<VacanteUI>();
  @Output() generateInterview = new EventEmitter<number>();

  activeTab = 'detalles';
  isApplying = false;
  hasApplied = false;

  // Solo necesitamos el ID para pasarlo al componente hijo
  sessionId = signal<number | null>(null);

  get tabs(): Tab[] {
    const baseTabs: Tab[] = [{ id: 'detalles', label: 'Detalles' }];

    if (this.viewMode === 'company') {
      baseTabs.push(
        { id: 'candidatos', label: `Candidatos (${this.vacancy.candidatos || 0})` },
        { id: 'ranking', label: 'Ranking' },
      );
    } else if (this.viewMode === 'candidate' && this.hasApplied) {
      baseTabs.push({ id: 'entrevista', label: 'Entrevista' });
    }

    return baseTabs;
  }

  ngOnInit() {
    document.body.style.overflow = 'hidden';
    if (this.viewMode === 'candidate') {
      this.checkApplicationStatus();
    }
  }

  ngOnDestroy() {
    document.body.style.overflow = '';
  }

  checkApplicationStatus() {
    this.interviewService.getActiveSession().subscribe({
      next: (data) => {
        if (data.session) {
          if (data.session.vacancy_id === this.vacancy.id) {
            this.hasApplied = true;
            this.sessionId.set(data.session.id);
          }
        }
      },
      error: (err) => console.error('Error checking application status:', err),
    });
  }

  onApply() {
    if (this.hasApplied) {
      this.activeTab = 'entrevista';
      return;
    }

    if (!this.vacancy.id) return;

    this.isApplying = true;

    this.vacanciesService.apply(this.vacancy.id).subscribe({
      next: (response) => {
        // Verificar si se creó la sesión
        if (response.interview_session && response.interview_session.id) {
          this.sessionId.set(response.interview_session.id);
          this.hasApplied = true;

          alert('¡Postulación exitosa! Puedes iniciar tu entrevista en la pestaña "Entrevista".');
          this.activeTab = 'entrevista';
        } else if (response.interview_session?.error) {
          alert(`Postulación exitosa, pero: ${response.interview_session.error}`);
        } else {
          alert('Postulación enviada exitosamente.');
          this.onClose();
        }
        this.isApplying = false;
      },
      error: (err) => {
        console.error('Error applying:', err);
        const errorMsg = err.error?.detail || 'Error al postular';
        alert(errorMsg);
        this.isApplying = false;
      },
    });
  }

  setActiveTab(tab: string) {
    this.activeTab = tab;
  }

  onClose() {
    this.close.emit();
  }

  onEdit() {
    this.edit.emit(this.vacancy);
  }

  onGenerateInterview() {
    if (!this.vacancy.id) return;
    this.generateInterview.emit(this.vacancy.id);
  }

  onBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      this.onClose();
    }
  }
}
