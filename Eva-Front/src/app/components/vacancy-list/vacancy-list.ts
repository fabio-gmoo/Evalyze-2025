import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VacancyCard } from '@widgets/vacancy-card/vacancy-card';
import { VacanteUI, ViewMode } from '@interfaces/vacante-model';

@Component({
  selector: 'app-vacancy-list',
  imports: [CommonModule, VacancyCard],
  templateUrl: './vacancy-list.html',
  styleUrl: './vacancy-list.scss',
})
export class VacancyList {
  @Input() vacancies: VacanteUI[] = [];
  @Input() viewMode: ViewMode = 'company';
  @Input() loading: boolean = false;
  @Input() canCreateVacancy: boolean = true;

  @Output() edit = new EventEmitter<VacanteUI>();
  @Output() delete = new EventEmitter<number>();
  @Output() apply = new EventEmitter<VacanteUI>();
  @Output() createNew = new EventEmitter<void>();
  @Output() details = new EventEmitter<VacanteUI>(); // New event

  onEdit(vacancy: VacanteUI): void {
    if (this.canCreateVacancy) {
      this.edit.emit(vacancy);
    }
  }

  onDelete(id: number): void {
    if (this.canCreateVacancy) {
      this.delete.emit(id);
    }
  }

  onApply(vacancy: VacanteUI): void {
    this.apply.emit(vacancy);
  }

  onCreateNew(): void {
    if (this.canCreateVacancy) {
      this.createNew.emit();
    }
  }

  onDetails(vacancy: VacanteUI): void {
    this.details.emit(vacancy);
  }
}
