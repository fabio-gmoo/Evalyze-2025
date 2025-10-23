import { Component, Input, Output, EventEmitter, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VacanteUI } from '@interfaces/vacante-model';
import { VacancyTabs } from '@components/vacancy-tabs/vacancy-tabs';
import { Tab, FormData } from '@interfaces/vacante-model';
import { Interview, CandidateChatStartResponse } from '@services/interview';
import { InterviewQuestion, GenerateInterviewResponse } from '@services/interview';
import { ChatModal } from '@components/chat-modal/chat-modal';
import { Vacancies } from '@services/vacancies';
import { Observable, of } from 'rxjs';
import { filter, map, catchError } from 'rxjs/operators';
import { Auth } from '@services/auth';
import { Me } from '@interfaces/token-types-dto';

@Component({
  selector: 'app-vacancy-details-modal',
  imports: [CommonModule, FormsModule, VacancyTabs, ChatModal],
  templateUrl: './vacancy-details-modal.html',
  styleUrl: './vacancy-details-modal.scss',
})
export class VacancyDetailsModal implements OnInit {
  private interviewService = inject(Interview);
  private vacanciesService = inject(Vacancies);
  private authService = inject(Auth);

  @Input() vacancy!: VacanteUI;
  @Input() viewMode: 'company' | 'candidate' = 'company';
  @Output() close = new EventEmitter<void>();
  @Output() apply = new EventEmitter<VacanteUI>();
  @Output() edit = new EventEmitter<VacanteUI>();
  @Output() generateInterview = new EventEmitter<number>();

  activeTab = 'detalles';

  isChatModalOpen = false;
  activeInterviewQuestions: InterviewQuestion[] | null = null;
  activeChatSessionId: string | null = null; // Store session ID
  activeInitialMessage: string | null = null;

  isApplying: boolean = false;
  isStartingChat: boolean = false;
  hasApplied: boolean = false;

  userIsCandidate: boolean = false;

  ngOnInit() {
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    this.checkUserStatusAndApplication();
  }

  ngOnDestroy() {
    document.body.style.overflow = '';
  }

  private checkUserStatusAndApplication(): void {
    this.authService.me$
      .pipe(
        filter((me: Me | null): me is Me => !!me && !!this.vacancy?.id),

        map((me: Me) => me.role === 'candidate'),
      )
      .subscribe((isCandidate) => {
        this.userIsCandidate = isCandidate;
        if (isCandidate) {
          this.vacanciesService
            .getMyApplications()
            .pipe(
              map((applications) =>
                applications.some((app: any) => app.vacancy_info.id === this.vacancy.id),
              ),
              catchError(() => {
                console.error('Failed to retrieve application status.');
                return of(false);
              }),
            )
            .subscribe((applied) => {
              this.hasApplied = applied;
            });
        }
      });
  }

  startCandidateChatSession(vacancyId: number): void {
    if (this.isStartingChat || !vacancyId) return;

    this.isStartingChat = true;
    this.activeInterviewQuestions = null;
    this.activeChatSessionId = null;
    this.activeInitialMessage = null;

    // *** THIS IS THE KEY CHANGE ***
    // Call the new dedicated candidate endpoint
    this.interviewService.startCandidateChat(vacancyId).subscribe({
      next: (response: CandidateChatStartResponse) => {
        // Set the chat state based on the backend response
        this.activeInterviewQuestions = response.questions;
        this.activeChatSessionId = response.session_id;
        this.activeInitialMessage = response.initial_message;

        this.isChatModalOpen = true; // Open the chat modal now
      },
      error: (err) => {
        console.error('Error starting candidate chat session:', err);
        alert('Error al iniciar la entrevista. Revisa los logs de los servicios.');
      },
      complete: () => {
        this.isStartingChat = false;
      },
    });
  }

  handleCandidateApplication(): void {
    if (!this.vacancy?.id || this.isApplying || this.isStartingChat || this.hasApplied) return;

    this.isApplying = true;

    this.vacanciesService.apply(this.vacancy.id).subscribe({
      next: (applicationResponse) => {
        // ... (Application successful logging) ...
        this.isApplying = false;
        this.hasApplied = true;

        // CORRECT CALL for immediate chat start
        this.startCandidateChatSession(this.vacancy.id!);
      },
      error: (err) => {
        this.isApplying = false; // Reset loading state

        const detail = err.error?.detail || '';

        if (this.vacancy.id && err.status === 400 && detail.includes('postulado')) {
          this.hasApplied = true;
          // If already applied, still try to start the chat
          this.startCandidateChatSession(this.vacancy.id!); // CORRECT CALL
        } else if (err.status === 401) {
          alert('⚠️ Debes iniciar sesión para postular a esta vacante');
        } else if (err.status === 403) {
          alert('⚠️ Solo los candidatos pueden postular a vacantes');
        } else {
          console.error('Unhandled error during application:', err);
          alert('❌ Error al postular. Por favor, intenta de nuevo.');
        }
      },
    });
  }
  get tabs(): Tab[] {
    const baseTabs: Tab[] = [{ id: 'detalles', label: 'Detalles' }];

    if (this.viewMode === 'company') {
      const candidateCount = this.vacancy.applications_count || this.vacancy.candidatos || 0;
      baseTabs.push({
        id: 'candidatos',
        label: `Candidatos (${candidateCount})`,
      });
    }

    return baseTabs;
  }

  onClose() {
    this.close.emit();
  }

  onApply() {
    this.apply.emit(this.vacancy);
  }

  onEdit() {
    this.edit.emit(this.vacancy);
  }

  setActiveTab(tab: string) {
    this.activeTab = tab;
  }

  onBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      this.onClose();
    }
  }

  onGenerateInterview() {
    if (!this.vacancy.id) return;

    this.generateInterview.emit(this.vacancy.id);
  }
}
