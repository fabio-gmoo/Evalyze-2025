import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Pregunta } from '@interfaces/vacante-model';

@Component({
  selector: 'app-ai-questions',
  imports: [CommonModule, FormsModule],
  templateUrl: './ai-questions.html',
  styleUrl: './ai-questions.scss',
})
export class AiQuestions {
  @Input() preguntas: Pregunta[] = [];
  @Output() preguntasChange = new EventEmitter<Pregunta[]>();
  @Output() add = new EventEmitter<void>();
  @Output() remove = new EventEmitter<number>();
  @Output() update = new EventEmitter<{ index: number; patch: Partial<Pregunta> }>();

  onAdd(): void {
    this.add.emit();
  }

  onRemove(index: number): void {
    this.remove.emit(index);
  }

  onUpdate(index: number, patch: Partial<Pregunta>): void {
    this.update.emit({ index, patch });
  }

  trackByPregunta = (_: number, item: Pregunta) => item.id;
}
