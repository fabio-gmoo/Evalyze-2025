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
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';
import { environment } from '@environment';
import { VacanteUI } from '@interfaces/vacante-model';
import { Interview, InterviewSession, ChatMessage } from '@services/interview';

@Component({
  selector: 'app-interview-chat',
  imports: [CommonModule, FormsModule],
  templateUrl: './interview-chat.html',
  styleUrl: './interview-chat.scss',
})
export class InterviewChat implements OnInit, OnDestroy, AfterViewChecked {
  @Input() sessionId: number | null = null;
  @Input() vacancy: VacanteUI | null = null;

  @ViewChild('messagesContainer') messagesContainer?: ElementRef<HTMLDivElement>;

  // Inyectamos el servicio para gestionar la comunicación
  private interviewService = inject(Interview);

  // Signals
  session = signal<InterviewSession | null>(null);
  messages = signal<ChatMessage[]>([]);
  draft = signal('');
  isTyping = signal(false);
  loading = signal(false);
  totalQuestions = signal(0);

  // Subscriptions
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

    // Usamos el servicio de entrevista
    this.interviewService.getSession(this.sessionId).subscribe({
      next: (data) => {
        this.session.set(data);
      },
      error: (err) => console.error('Error loading session:', err),
    });
  }

  loadMessages() {
    if (!this.sessionId) return;

    // Usamos el servicio de entrevista (que ya apunta a la ruta /chat-messages/ o /chat-history/)
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

    // Usamos el servicio de entrevista
    this.interviewService.startSession(this.sessionId).subscribe({
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

        this.shouldScroll = true;
      },
      error: (err) => {
        this.loading.set(false);
        console.error('Error starting interview:', err);
        // alert('Error al iniciar la entrevista. Por favor intenta de nuevo.');
      },
    });
  }

  sendMessage() {
    const message = this.draft().trim();
    if (!message || !this.sessionId) return;

    // Add candidate message immediately
    const candidateMsg: ChatMessage = {
      sender: 'candidate',
      content: message,
      timestamp: new Date().toISOString(),
    };
    this.messages.update((msgs) => [...msgs, candidateMsg]);
    this.draft.set('');
    this.isTyping.set(true);
    this.shouldScroll = true;

    // Usamos el servicio de entrevista
    this.interviewService.sendMessage(this.sessionId, message).subscribe({
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
          this.stopPolling();
        } else {
          this.session.update((s) =>
            s
              ? {
                  ...s,
                  current_question_index: data.current_question,
                }
              : null,
          );
        }

        this.shouldScroll = true;
      },
      error: (err) => {
        this.isTyping.set(false);
        console.error('Error sending message:', err);
        // alert('Error al enviar el mensaje. Por favor intenta de nuevo.');
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
    // Poll every 5 seconds for updates
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
