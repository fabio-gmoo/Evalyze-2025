import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VacanteUI, ViewMode } from '@interfaces/vacante-model';

@Component({
  selector: 'app-vacancy-card',
  imports: [CommonModule],
  templateUrl: './vacancy-card.html',
  styleUrl: './vacancy-card.scss',
})
export class VacancyCard {
  @Input() vacancy!: VacanteUI;
  @Input() viewMode: ViewMode = 'company';
  @Output() edit = new EventEmitter<VacanteUI>();
  @Output() delete = new EventEmitter<number>();
  @Output() apply = new EventEmitter<VacanteUI>();
  @Output() details = new EventEmitter<VacanteUI>();

  onEdit(): void {
    this.edit.emit(this.vacancy);
  }

  onDelete(): void {
    if (this.vacancy.id) {
      this.delete.emit(this.vacancy.id);
    }
  }

  onApply(): void {
    this.apply.emit(this.vacancy);
  }

  onDetails() {
    this.details.emit(this.vacancy);
  }
}
