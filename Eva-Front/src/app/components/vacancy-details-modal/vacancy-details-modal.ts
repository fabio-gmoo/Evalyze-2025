import { Component, Input, Output, EventEmitter, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { VacanteUI } from '@interfaces/vacante-model';
import { VacancyTabs } from '@components/vacancy-tabs/vacancy-tabs';
import { Tab, FormData } from '@interfaces/vacante-model';
import { Interview } from '@services/interview';
import { InterviewQuestion, InterviewSession, ChatMessage } from '@services/interview';
import { ChatModal } from '@components/chat-modal/chat-modal';
import { Vacancies } from '@services/vacancies';
import { Observable, of } from 'rxjs';
import { filter, map, catchError } from 'rxjs/operators';
import { Auth } from '@services/auth';
import { Me } from '@interfaces/token-types-dto';

import { InterviewChat } from '@components/interview-chat/interview-chat';

@Component({
  selector: 'app-vacancy-details-modal',
  imports: [CommonModule, FormsModule, VacancyTabs, InterviewChat],
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
  isApplying = false;
  hasApplied = false;

  // Interview state
  sessionId = signal<number | null>(null);
  session = signal<InterviewSession | null>(null);
  messages = signal<ChatMessage[]>([]);
  draft = signal('');
  isTyping = signal(false);
  loading = signal(false);
  totalQuestions = signal(0);
  private scrollScheduled = false;

  get tabs(): Tab[] {
    const baseTabs: Tab[] = [{ id: 'detalles', label: 'Detalles' }];

    if (this.viewMode === 'company') {
      baseTabs.push(
        {
          id: 'candidatos',
          label: `Candidatos (${this.vacancy.candidatos || 0})`,
        },
        {
          id: 'ranking',
          label: 'Ranking',
        },
      );
    } else if (this.viewMode === 'candidate' && this.hasApplied) {
      // Add chat tab only if candidate has applied
      baseTabs.push({
        id: 'entrevista',
        label: 'Entrevista',
      });
    }

    return baseTabs;
  }

  ngOnInit() {
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';

    // Check if candidate has an active interview session
    if (this.viewMode === 'candidate') {
      this.checkApplicationStatus();
    }
  }

  ngOnDestroy() {
    document.body.style.overflow = '';
  }

  checkApplicationStatus() {
    // Check if user has applied to this vacancy
    this.interviewService.getActiveSession().subscribe({
      next: (data) => {
        if (data.session) {
          const sessionVacancyTitle = data.session.vacancy_title;
          if (sessionVacancyTitle === this.vacancy.puesto) {
            this.hasApplied = true;
            this.sessionId.set(data.session.id);
            this.session.set(data.session);
            this.loadMessages();
          }
        }
      },
      error: (err) => console.error('Error checking application status:', err),
    });
  }
  onClose() {
    this.close.emit();
  }

  onApply() {
    if (this.hasApplied) {
      // Already applied, switch to interview tab
      this.activeTab = 'entrevista';
      return;
    }

    // Apply to vacancy
    if (!this.vacancy.id) return;

    this.isApplying = true;

    this.vacanciesService.apply(this.vacancy.id).subscribe({
      next: (response) => {
        console.log('Application successful:', response);

        // Check if interview session was created
        if (response.interview_session && response.interview_session.id) {
          this.sessionId.set(response.interview_session.id);
          this.session.set({
            id: response.interview_session.id,
            status: 'pending',
            current_question_index: 0,
            last_activity: new Date().toISOString(),
            total_score: 0,
            max_possible_score: 100,
            candidate_name: '',
            vacancy_title: this.vacancy.puesto,
            message_count: 0,
          } as InterviewSession);
          this.hasApplied = true;

          // Load the interview data
          this.loadSession();

          // Show success and switch to interview tab
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
  onEdit() {
    this.edit.emit(this.vacancy);
  }

  setActiveTab(tab: string) {
    this.activeTab = tab;

    // If switching to interview tab, scroll to bottom
    if (tab === 'entrevista' && this.messages().length > 0) {
      setTimeout(() => this.scrollToBottom(), 100);
    }
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

  loadSession() {
    const id = this.sessionId();
    if (!id) return;

    this.interviewService.getSession(id).subscribe({
      next: (data) => {
        this.session.set(data);
        this.loadMessages();
      },
      error: (err) => {
        console.error('Error loading session:', err);
      },
    });
  }

  loadMessages() {
    const id = this.sessionId();
    if (!id) return;

    this.interviewService.getMessages(id).subscribe({
      next: (data) => {
        this.messages.set(data.messages || []);
        this.totalQuestions.set(data.total_questions || 0);
        this.scheduleScroll();
      },
      error: (err) => {
        console.error('Error loading messages:', err);
      },
    });
  }

  startInterview() {
    const id = this.sessionId();
    if (!id) return;

    this.loading.set(true);

    this.interviewService.startSession(id).subscribe({
      next: (data) => {
        this.loading.set(false);

        // Add first message
        if (data.first_message) {
          const firstMsg: ChatMessage = {
            sender: 'ai',
            content: data.first_message,
            timestamp: new Date().toISOString(),
          };
          this.messages.update((msgs) => [...msgs, firstMsg]);
        }

        // Update session status
        this.session.update((s) => (s ? { ...s, status: 'active' } : null));

        this.scheduleScroll();
      },
      error: (err) => {
        this.loading.set(false);
        console.error('Error starting interview:', err);
        alert('Error al iniciar la entrevista');
      },
    });
  }

  sendMessage() {
    const message = this.draft().trim();
    const id = this.sessionId();
    if (!message || !id) return;

    // Add candidate message immediately
    const candidateMsg: ChatMessage = {
      sender: 'candidate',
      content: message,
      timestamp: new Date().toISOString(),
    };
    this.messages.update((msgs) => [...msgs, candidateMsg]);
    this.draft.set('');
    this.isTyping.set(true);
    this.scheduleScroll();

    this.interviewService.sendMessage(id, message).subscribe({
      next: (data) => {
        this.isTyping.set(false);

        // Add AI response
        const aiMsg: ChatMessage = {
          sender: 'ai',
          content: data.message,
          timestamp: new Date().toISOString(),
        };
        this.messages.update((msgs) => [...msgs, aiMsg]);

        // Update session
        if (data.is_complete) {
          this.session.update((s) => (s ? { ...s, status: 'completed' } : null));
        } else {
          this.session.update((s) =>
            s ? { ...s, current_question_index: data.current_question } : null,
          );
        }

        this.scheduleScroll();
      },
      error: (err) => {
        this.isTyping.set(false);
        console.error('Error sending message:', err);
        alert('Error al enviar el mensaje');
      },
    });
  }

  getStatusLabel(status?: string): string {
    const labels: Record<string, string> = {
      pending: 'Pendiente',
      active: 'En Progreso',
      completed: 'Completada',
      abandoned: 'Abandonada',
    };
    return labels[status || ''] || status || '';
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  private scheduleScroll() {
    if (!this.scrollScheduled) {
      this.scrollScheduled = true;
      setTimeout(() => {
        this.scrollToBottom();
        this.scrollScheduled = false;
      }, 100);
    }
  }

  private scrollToBottom() {
    const messagesArea = document.querySelector('.messages-area');
    if (messagesArea) {
      messagesArea.scrollTop = messagesArea.scrollHeight;
    }
  }
}
