import {
  Component,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  ElementRef,
  AfterViewChecked,
  OnChanges,
  SimpleChanges,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatMessage, VacanteUI } from '@interfaces/vacante-model';
import { InterviewQuestion, InterviewData, Interview } from '@services/interview'; // Assuming path
import { Chat, ChatMessageResponse, ChatStartResponse } from '@services/chat'; // Assuming path
import { getCurrentTime } from '@interfaces/vacancy-utils'; // Assuming path

@Component({
  selector: 'app-chat-modal',
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-modal.html',
  styleUrl: './chat-modal.scss',
})
export class ChatModal implements AfterViewChecked, OnChanges {
  @Input() open: boolean = false;
  @Input() vacancy: VacanteUI | null = null;
  @Input() interviewQuestions: InterviewQuestion[] | null = null; // New input for initial questions

  @Output() close = new EventEmitter<void>();

  @ViewChild('chatScroll') chatScroll?: ElementRef<HTMLDivElement>;

  private chatService = inject(Chat);

  messages: ChatMessage[] = [];
  draft: string = '';
  sessionId: string | null = null;
  isLoading: boolean = false;
  isChatActive: boolean = false;

  private shouldScroll = false;

  // --- Lifecycle and State Management ---

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open'] && changes['open'].currentValue === true) {
      this.shouldScroll = true;
      if (!this.isChatActive && this.interviewQuestions) {
        this.startConversation();
      }
    } else if (changes['open'] && changes['open'].currentValue === false) {
      // Optional: Reset state when closing, or keep history
      // this.resetChat();
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  private resetChat(): void {
    this.messages = [];
    this.sessionId = null;
    this.draft = '';
    this.isLoading = false;
    this.isChatActive = false;
  }

  // --- Chat Logic ---

  private buildInitialPrompt(): string {
    if (!this.interviewQuestions) return 'Inicia la conversación como un entrevistador amigable.';

    const questions = this.interviewQuestions.map((q) => `- ${q.question}`).join('\n');
    const systemInstruction = `Eres un entrevistador de IA. Tu tarea es guiar al candidato a través de las siguientes preguntas de la vacante '${this.vacancy?.puesto}':\n${questions}\n\nComienza la conversación con un saludo cálido, introduce la vacante y haz la primera pregunta de la lista.`;
    return systemInstruction;
  }

  startConversation(): void {
    this.isLoading = true;
    this.messages = [{ from: 'bot', text: 'Preparando entrevista...', time: getCurrentTime() }];

    const initialSystemPrompt = this.buildInitialPrompt();

    // Call the service to get a session ID and the first message
    this.chatService.startSession(initialSystemPrompt).subscribe({
      next: (response) => {
        this.sessionId = response.session_id;
        this.messages.pop(); // Remove "Preparando entrevista..."
        this.addBotMessage(response.message);
        this.isChatActive = true;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error starting chat session:', err);
        this.addBotMessage(
          'Hubo un error al iniciar la conversación con la IA. Por favor, inténtalo de nuevo.',
        );
        this.isLoading = false;
      },
    });
  }

  onSend(event: Event): void {
    event.preventDefault();
    const msg = (this.draft || '').trim();
    if (!msg || !this.sessionId || this.isLoading) return;

    this.addMessage({ from: 'user', text: msg, time: getCurrentTime() });
    this.draft = '';
    this.isLoading = true;
    this.shouldScroll = true;

    this.chatService.sendMessage(this.sessionId, msg).subscribe({
      next: (response) => {
        this.addBotMessage(response.message);
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error sending message:', err);
        this.addBotMessage('Perdón, no pude procesar tu respuesta. Intenta de nuevo.');
        this.isLoading = false;
      },
    });
  }

  // --- Utility Methods ---

  addMessage(message: ChatMessage): void {
    this.messages = [...this.messages, message];
  }

  addBotMessage(text: string): void {
    // Add a small delay to simulate processing time before showing the bot response
    setTimeout(() => {
      this.messages = [...this.messages, { from: 'bot', text: text, time: getCurrentTime() }];
      this.shouldScroll = true;
    }, 500);
  }

  onDraftChange(value: string): void {
    this.draft = value;
  }

  onClose(): void {
    this.close.emit();
  }

  private scrollToBottom(): void {
    try {
      this.chatScroll?.nativeElement.scrollTo({
        top: this.chatScroll.nativeElement.scrollHeight,
        behavior: 'smooth',
      });
    } catch (err) {
      // Prevent crash if element is not yet rendered
    }
  }

  trackByIndex = (_index: number) => _index;
}
