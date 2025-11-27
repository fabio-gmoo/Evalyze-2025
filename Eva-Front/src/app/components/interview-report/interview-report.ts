import { Component, Input, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Analysis, InterviewReport } from '@services/analysis';

@Component({
  selector: 'app-interview-report',
  imports: [CommonModule],
  templateUrl: './interview-report.html',
  styleUrl: './interview-report.scss',
})
export class InterviewReport implements OnInit {
  private analysisService = inject(Analysis);

  @Input() sessionId: number | null = null;
  @Input() reportData: InterviewReport | null = null;

  report = signal<InterviewReport | null>(null);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  ngOnInit() {
    if (this.reportData) {
      this.report.set(this.reportData);
    } else if (this.sessionId) {
      this.loadReport();
    }
  }

  loadReport() {
    if (!this.sessionId) return;

    this.loading.set(true);
    this.error.set(null);

    this.analysisService.getReport(this.sessionId).subscribe({
      next: (data) => {
        this.report.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading report:', err);
        this.error.set(err.error?.detail || 'Error al cargar el análisis');
        this.loading.set(false);
      },
    });
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }

  getRecommendationClass(rec: string): string {
    const lower = rec.toLowerCase();
    if (lower.includes('strongly recommend') || lower.includes('excellent')) {
      return 'positive';
    }
    if (lower.includes('not recommended') || lower.includes('significant')) {
      return 'critical';
    }
    return '';
  }
}
