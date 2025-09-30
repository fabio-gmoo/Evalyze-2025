import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-stats-strip',
  standalone: true,
  templateUrl: './stats-strip.html',
  styleUrl: './stats-strip.scss',
})
export class StatsStrip {
  @Input() active: number = 0;
  @Input() candidates: number = 0;
  @Input() interviews: number = 0;
  @Input() hires: number = 0;
}
