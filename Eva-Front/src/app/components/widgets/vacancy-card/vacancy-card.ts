import { Component, Input } from '@angular/core';
import { Vacancy } from '@interfaces/vacancy';

@Component({
  selector: 'app-vacancy-card',
  standalone: true,
  templateUrl: './vacancy-card.html',
  styleUrl: './vacancy-card.scss',
})
export class VacancyCard {
  @Input({ required: true }) vacancy!: Vacancy;
}
