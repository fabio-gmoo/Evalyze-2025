import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FormData } from '@interfaces/vacante-model';

@Component({
  selector: 'app-vacancy-form',
  imports: [CommonModule, FormsModule],
  templateUrl: './vacancy-form.html',
  styleUrl: './vacancy-form.scss',
})
export class VacancyForm {
  @Input() formData!: FormData;
  @Input() loading: boolean = false;

  @Output() formDataChange = new EventEmitter<FormData>();
  @Output() generateWithAI = new EventEmitter<void>();
  @Output() fieldUpdate = new EventEmitter<{ field: keyof FormData; value: string | number }>();
  @Output() arrayItemUpdate = new EventEmitter<{
    field: 'requisitos' | 'responsabilidades';
    index: number;
    value: string;
  }>();
  @Output() arrayItemAdd = new EventEmitter<'requisitos' | 'responsabilidades'>();
  @Output() arrayItemRemove = new EventEmitter<{
    field: 'requisitos';
    index: number;
  }>();

  onFieldUpdate(field: keyof FormData, value: string | number): void {
    this.fieldUpdate.emit({ field, value });
  }

  onArrayItemUpdate(field: 'requisitos', index: number, value: string): void {
    this.arrayItemUpdate.emit({ field, index, value });
  }

  onArrayItemAdd(field: 'requisitos'): void {
    this.arrayItemAdd.emit(field);
  }

  onArrayItemRemove(field: 'requisitos', index: number): void {
    this.arrayItemRemove.emit({ field, index });
  }

  onGenerateWithAI(): void {
    this.generateWithAI.emit();
  }

  trackByIndex = (_index: number) => _index;
}
