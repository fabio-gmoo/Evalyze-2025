import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  inject,
  signal,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  numberAttribute,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { interval, Subscription } from 'rxjs';
import { VacanteUI } from '@interfaces/vacante-model';
import { Interview, InterviewSession, ChatMessage } from '@services/interview';
import { Analysis } from '@services/analysis';
import { Router } from '@angular/router';

@Component({
  selector: 'app-interview-chat',
  imports: [CommonModule, FormsModule],
  templateUrl: './interview-chat.html',
  styleUrl: './interview-chat.scss',
})
export class InterviewChat implements OnInit, OnDestroy, AfterViewChecked {
  @Input({ transform: numberAttribute }) sessionId: number | null = null;
  @Input() vacancy: VacanteUI | null = null;

  @ViewChild('messagesContainer') messagesContainer?: ElementRef<HTMLDivElement>;

  private interviewService = inject(Interview);
  private analysisService = inject(Analysis);
  public router = inject(Router);

  // Signals
  session = signal<InterviewSession | null>(null);
  messages = signal<ChatMessage[]>([]);
  draft = signal('');
  isTyping = signal(false);
  loading = signal(false);
  totalQuestions = signal(0);

  // NEW: Finalization state
  isFinalizing = signal(false);
  showFinalizeConfirm = signal(false);

  private pollSubscription?: Subscription;
  private shouldScroll = false;

  ngOnInit() {
    if (this.sessionId) {
      this.loadSession();
      this.loadMessages();
      this.startPolling();
    }
  }

  ngOnDestroy() {
    this.stopPolling();
  }

  ngAfterViewChecked() {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  loadSession() {
    if (!this.sessionId) return;
    this.interviewService.getSession(this.sessionId).subscribe({
      next: (data) => {
        this.session.set(data);
      },
      error: (err) => console.error('Error loading session:', err),
    });
  }

  loadMessages() {
    if (!this.sessionId) return;
    this.interviewService.getMessages(this.sessionId).subscribe({
      next: (data) => {
        this.messages.set(data.messages || []);
        this.totalQuestions.set(data.total_questions || 0);
        this.shouldScroll = true;
      },
      error: (err) => console.error('Error loading messages:', err),
    });
  }

  startInterview() {
    if (!this.sessionId) return;
    this.loading.set(true);

    this.interviewService.startSession(this.sessionId).subscribe({
      next: (data) => {
        this.loading.set(false);
        if (data.first_message) {
          const firstMsg: ChatMessage = {
            sender: 'ai',
            content: data.first_message,
            timestamp: new Date().toISOString(),
          };
          this.messages.update((msgs) => [...msgs, firstMsg]);
        }
        this.session.update((s) => (s ? { ...s, status: 'active' } : null));
        this.shouldScroll = true;
      },
      error: (err) => {
        this.loading.set(false);
        console.error('Error starting interview:', err);
      },
    });
  }

  sendMessage() {
    const message = this.draft().trim();
    if (!message || !this.sessionId) return;

    const candidateMsg: ChatMessage = {
      sender: 'candidate',
      content: message,
      timestamp: new Date().toISOString(),
    };
    this.messages.update((msgs) => [...msgs, candidateMsg]);
    this.draft.set('');
    this.isTyping.set(true);
    this.shouldScroll = true;

    this.interviewService.sendMessage(this.sessionId, message).subscribe({
      next: (data) => {
        this.isTyping.set(false);
        const aiMsg: ChatMessage = {
          sender: 'ai',
          content: data.message,
          timestamp: new Date().toISOString(),
        };
        this.messages.update((msgs) => [...msgs, aiMsg]);

        if (data.is_complete) {
          this.session.update((s) => (s ? { ...s, status: 'completed' } : null));
          this.stopPolling();
        } else {
          this.session.update((s) =>
            s ? { ...s, current_question_index: data.current_question } : null,
          );
        }
        this.shouldScroll = true;
      },
      error: (err) => {
        this.isTyping.set(false);
        console.error('Error sending message:', err);
      },
    });
  }

  // NEW: Finalize interview methods
  showFinalizeDialog() {
    this.showFinalizeConfirm.set(true);
  }

  cancelFinalize() {
    this.showFinalizeConfirm.set(false);
  }

  finalizeInterview() {
    if (!this.sessionId) return;

    this.isFinalizing.set(true);
    this.showFinalizeConfirm.set(false);

    this.analysisService.finalizeInterview(this.sessionId).subscribe({
      next: (response) => {
        this.isFinalizing.set(false);

        // Update session status
        this.session.update((s) => (s ? { ...s, status: 'completed' } : null));

        // Show success message
        alert(`¡Entrevista finalizada! Tu puntuación: ${response.score}%`);

        // Navigate to results
        this.router.navigate(['/interview-results', this.sessionId]);
      },
      error: (err) => {
        this.isFinalizing.set(false);
        console.error('Error finalizing interview:', err);
        alert('Error al finalizar la entrevista. Por favor intenta de nuevo.');
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

  private scrollToBottom() {
    try {
      if (this.messagesContainer) {
        const element = this.messagesContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    } catch (err) {
      console.error('Scroll error:', err);
    }
  }

  private startPolling() {
    this.pollSubscription = interval(5000).subscribe(() => {
      if (this.session()?.status === 'active') {
        this.loadMessages();
      }
    });
  }

  private stopPolling() {
    this.pollSubscription?.unsubscribe();
  }
}
