import { Component, Input } from '@angular/core';
import { Vacancy } from '@interfaces/vacancy';

@Component({
  selector: 'app-vacancy-card',
  standalone: true,
  templateUrl: './vacancy-card.html',
  styleUrl: './vacancy-card.scss',
})
export class VacancyCard {
  vacante = input.required<VacanteUI>();
  edit = output<VacanteUI>();
  deleteClick = output<number>();
}
