import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  inject,
  signal,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VacanteUI, Tab } from '@interfaces/vacante-model';
import { VacancyTabs } from '@components/vacancy-tabs/vacancy-tabs';
import { InterviewChat } from '@components/interview-chat/interview-chat';
import { InterviewReportC } from '@components/interview-report/interview-report';
import { Interview } from '@services/interview';
import { Vacancies } from '@services/vacancies';

@Component({
  selector: 'app-vacancy-details-modal',
  imports: [CommonModule, FormsModule, VacancyTabs, InterviewChat, InterviewReportC],
  templateUrl: './vacancy-details-modal.html',
  styleUrl: './vacancy-details-modal.scss',
})
export class VacancyDetailsModal implements OnInit {
  private interviewService = inject(Interview);
  private vacanciesService = inject(Vacancies);
  private cd = inject(ChangeDetectorRef);

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
  
  // ✅ CAMBIO: Usamos signal para asegurar reactividad
  showResults = signal(false);

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
    
    // ✅ CAMBIO: Leemos la señal con paréntesis ()
    if (this.showResults()) {
      baseTabs.push({ id: 'resultados', label: 'Resultados' });
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
            
            // ✅ CAMBIO: Actualizamos la señal
            if (data.session.status === 'completed') {
              this.showResults.set(true);
            }
            
            this.cd.markForCheck();
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
        if (response.interview_session && response.interview_session.id) {
          this.sessionId.set(response.interview_session.id);
          this.hasApplied = true;
          this.activeTab = 'entrevista';
          this.cd.detectChanges();
          alert('¡Postulación exitosa! Puedes iniciar tu entrevista en la pestaña "Entrevista".');
        } else if (response.interview_session?.error) {
          alert(`Postulación exitosa, pero: ${response.interview_session.error}`);
        } else {
          alert('Postulación enviada exitosamente.');
          this.onClose();
        }
        this.isApplying = false;
        this.cd.markForCheck();
      },
      error: (err) => {
        console.error('Error applying:', err);
        const errorMsg = err.error?.detail || 'Error al postular';
        alert(errorMsg);
        this.isApplying = false;
        this.cd.markForCheck();
      },
    });
  }

  // ✅ CAMBIO: Método reactivo
  onInterviewFinished() {
    console.log('Evento finished recibido, mostrando resultados...');
    this.showResults.set(true); // Activamos la señal
    this.activeTab = 'resultados'; // Cambiamos pestaña
    this.cd.detectChanges(); // Forzamos actualización visual
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