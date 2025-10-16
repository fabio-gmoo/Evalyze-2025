import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VacancyForm } from '@components/vacancy-form/vacancy-form';
import { AiQuestions } from '@components/ai-questions/ai-questions';
import { FormData, Pregunta, VacanteUI } from '@interfaces/vacante-model';

@Component({
  selector: 'app-vacancy-modal',
  imports: [CommonModule, AiQuestions, VacancyForm],
  templateUrl: './vacancy-modal.html',
  styleUrl: './vacancy-modal.scss',
})
export class VacancyModal {
  @Input() show: boolean = false;
  @Input() editingVacante: VacanteUI | null = null;
  @Input() formData!: FormData;
  @Input() preguntas: Pregunta[] = [];
  @Input() loading: boolean = false;
  @Input() duracion: number = 45;
  @Input() puntuacionMinima: number = 75;

  @Output() close = new EventEmitter<void>();
  @Output() save = new EventEmitter<void>();
  @Output() generateWithAI = new EventEmitter<void>();
  @Output() fieldUpdate = new EventEmitter<{ field: keyof FormData; value: string | number }>();
  @Output() arrayItemUpdate = new EventEmitter<{
    field: 'requisitos';
    index: number;
    value: string;
  }>();
  @Output() arrayItemAdd = new EventEmitter<'requisitos'>();
  @Output() arrayItemRemove = new EventEmitter<{
    field: 'requisitos';
    index: number;
  }>();
  @Output() preguntaAdd = new EventEmitter<void>();
  @Output() preguntaRemove = new EventEmitter<number>();
  @Output() preguntaUpdate = new EventEmitter<{ index: number; patch: Partial<Pregunta> }>();

  onClose(): void {
    this.close.emit();
  }

  onSave(): void {
    this.save.emit();
  }

  onGenerateWithAI(): void {
    this.generateWithAI.emit();
  }

  onFieldUpdate(event: { field: keyof FormData; value: string | number }): void {
    this.fieldUpdate.emit(event);
  }

  onArrayItemUpdate(event: { field: 'requisitos'; index: number; value: string }): void {
    this.arrayItemUpdate.emit(event);
  }

  onArrayItemAdd(field: 'requisitos'): void {
    this.arrayItemAdd.emit(field);
  }

  onArrayItemRemove(event: { field: 'requisitos'; index: number }): void {
    this.arrayItemRemove.emit(event);
  }

  onPreguntaAdd(): void {
    this.preguntaAdd.emit();
  }

  onPreguntaRemove(index: number): void {
    this.preguntaRemove.emit(index);
  }

  onPreguntaUpdate(event: { index: number; patch: Partial<Pregunta> }): void {
    this.preguntaUpdate.emit(event);
  }
}
