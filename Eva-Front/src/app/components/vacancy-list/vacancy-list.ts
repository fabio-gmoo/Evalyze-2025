import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VacancyCard } from '@components/vacancy-card/vacancy-card';
import { VacanteUI, ViewMode } from '@interfaces/vacancte-model';

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

  @Output() edit = new EventEmitter<VacanteUI>();
  @Output() delete = new EventEmitter<number>();
  @Output() apply = new EventEmitter<VacanteUI>();
  @Output() createNew = new EventEmitter<void>();

  onEdit(vacancy: VacanteUI): void {
    this.edit.emit(vacancy);
  }

  onDelete(id: number): void {
    this.delete.emit(id);
  }

  onApply(vacancy: VacanteUI): void {
    this.apply.emit(vacancy);
  }

  onCreateNew(): void {
    this.createNew.emit();
  }
}
