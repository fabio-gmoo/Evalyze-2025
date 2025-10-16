import { Component, Input } from '@angular/core';
import { ViewMode } from '@interfaces/vacante-model';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-vacancy-header',
  imports: [CommonModule],
  templateUrl: './vacancy-header.html',
  styleUrl: './vacancy-header.scss',
})
export class VacancyHeader {
  @Input() viewMode: ViewMode = 'company';
}
