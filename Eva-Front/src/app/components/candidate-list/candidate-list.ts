import { Component, Input, Output, EventEmitter, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Vacancies } from '@services/vacancies';

@Component({
  selector: 'app-candidate-list',
  imports: [CommonModule],
  templateUrl: './candidate-list.html',
  styleUrl: './candidate-list.scss',
})
export class CandidateList implements OnInit {
  private vacanciesService = inject(Vacancies);

  @Input({ required: true }) vacancyId!: number;
  @Output() viewReport = new EventEmitter<number>();

  candidates = signal<any[]>([]);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  ngOnInit() {
    this.loadCandidates();
  }

  loadCandidates() {
    this.loading.set(true);
    this.vacanciesService.getApplications(this.vacancyId).subscribe({
      next: (data) => {
        this.candidates.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading candidates:', err);
        this.error.set('No se pudieron cargar los candidatos.');
        this.loading.set(false);
      },
    });
  }

  onViewReport(session: any) {
    if (session && session.id) {
      this.viewReport.emit(session.id);
    } else {
      alert('Este candidato aún no tiene una entrevista registrada.');
    }
  }
}
