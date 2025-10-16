import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatCard } from '@interfaces/vacante-model';
@Component({
  selector: 'app-stats-grid',
  imports: [CommonModule],
  templateUrl: './stats-grid.html',
  styleUrl: './stats-grid.scss',
})
export class StatsGrid {
  @Input() stats: StatCard[] = [];
}
