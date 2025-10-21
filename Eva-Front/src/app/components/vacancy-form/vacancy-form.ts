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
  @Output() arrayItemUpdate = new EventEmitter<{ index: number; value: string }>();
  @Output() arrayItemAdd = new EventEmitter<void>();
  @Output() arrayItemRemove = new EventEmitter<number>();

  onFieldUpdate(field: keyof FormData, value: string | number): void {
    this.fieldUpdate.emit({ field, value });
  }

  onArrayItemUpdate(index: number, value: string): void {
    this.arrayItemUpdate.emit({ index, value });
  }

  onArrayItemAdd(): void {
    this.arrayItemAdd.emit();
  }

  onArrayItemRemove(index: number): void {
    this.arrayItemRemove.emit(index);
  }

  onGenerateWithAI(): void {
    this.generateWithAI.emit();
  }

  trackByIndex = (_index: number) => _index;
}
