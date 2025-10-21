import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VacancyForm } from '@components/vacancy-form/vacancy-form';

import { FormData, Pregunta, VacanteUI } from '@interfaces/vacante-model';

@Component({
  selector: 'app-vacancy-modal',
  imports: [CommonModule, VacancyForm],
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
  @Output() arrayItemUpdate = new EventEmitter<{ index: number; value: string }>();
  @Output() arrayItemAdd = new EventEmitter<void>();
  @Output() arrayItemRemove = new EventEmitter<number>();
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

  onArrayItemUpdate(event: { index: number; value: string }): void {
    this.arrayItemUpdate.emit(event);
  }

  onArrayItemAdd(): void {
    this.arrayItemAdd.emit();
  }

  onArrayItemRemove(index: number): void {
    this.arrayItemRemove.emit(index);
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
