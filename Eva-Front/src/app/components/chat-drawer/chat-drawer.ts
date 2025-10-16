import {
  Component,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  ElementRef,
  AfterViewChecked,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatMessage, VacanteUI } from '@interfaces/vacante-model';

@Component({
  selector: 'app-chat-drawer',
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-drawer.html',
  styleUrl: './chat-drawer.scss',
})
export class ChatDrawer implements AfterViewChecked {
  @Input() open: boolean = false;
  @Input() messages: ChatMessage[] = [];
  @Input() vacancy: VacanteUI | null = null;
  @Input() draft: string = '';

  @Output() close = new EventEmitter<void>();
  @Output() send = new EventEmitter<string>();
  @Output() draftChange = new EventEmitter<string>();

  @ViewChild('chatScroll') chatScroll?: ElementRef<HTMLDivElement>;

  private shouldScroll = false;

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  onClose(): void {
    this.close.emit();
  }

  onSend(event: Event): void {
    event.preventDefault();
    const msg = (this.draft || '').trim();
    if (!msg) return;
    this.send.emit(msg);
    this.shouldScroll = true;
  }

  onDraftChange(value: string): void {
    this.draftChange.emit(value);
  }

  private scrollToBottom(): void {
    try {
      this.chatScroll?.nativeElement.scrollTo({
        top: this.chatScroll.nativeElement.scrollHeight,
        behavior: 'smooth',
      });
    } catch (err) {
      console.error('Scroll error:', err);
    }
  }

  trackByIndex = (_index: number) => _index;
}
