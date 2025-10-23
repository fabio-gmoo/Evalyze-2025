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
  @Input() sessionIdInput: string | null = null; // <--- NEW

  @Input() initialMessageInput: string | null = null;

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
    const wasOpened = changes['open'] && changes['open'].currentValue === true;
    const sessionArrived = changes['sessionIdInput'] && this.sessionIdInput;

    if (wasOpened) {
      this.resetChat();
      // When opened, we immediately set shouldScroll to true
      this.shouldScroll = true;
    }

    // LOGIC CHANGE: If the modal is open AND the session data is passed from the parent,
    // initialize the chat without calling the service.
    if (this.open && sessionArrived && this.initialMessageInput && !this.isChatActive) {
      this.sessionId = this.sessionIdInput;
      this.messages = []; // Clear the messages only here, just before adding the first real one.
      this.addBotMessage(this.initialMessageInput, 0); // Add the initial message immediately (delay 0)
      this.isChatActive = true;
      this.isLoading = false;
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  private resetChat(): void {
    // We only reset the core state, but keep the messages if the chat was already started.
    // If you want to clear history every time, uncomment the line below.
    // this.messages = [];
    this.sessionId = null;
    this.draft = '';
    this.isLoading = false;
    this.isChatActive = false;
  }

  // --- Chat Logic ---

  onSend(event: Event): void {
    event.preventDefault();
    const msg = (this.draft || '').trim();
    if (!msg || !this.sessionId || this.isLoading) return;

    this.addMessage({ from: 'user', text: msg, time: getCurrentTime() });
    this.draft = '';
    this.isLoading = true;
    this.shouldScroll = true;

    this.chatService.sendMessage(this.sessionId, msg).subscribe({
      next: (response: ChatMessageResponse) => {
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

  addBotMessage(text: string, delay: number = 500): void {
    const effectiveDelay = delay === 0 ? 0 : 500;

    setTimeout(() => {
      this.messages = [...this.messages, { from: 'bot', text: text, time: getCurrentTime() }];
      this.shouldScroll = true;
    }, effectiveDelay);
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
