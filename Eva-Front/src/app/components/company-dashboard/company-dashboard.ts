// Eva-Front/src/app/pages/company-dashboard/company-dashboard.ts

import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Analysis, CandidateInfo, RankedCandidate, GlobalReport } from '@services/analysis';
import { InterviewReport } from '@components/interview-report/interview-report';
import { Router } from '@angular/router';

@Component({
  selector: 'app-company-dashboard',
  standalone: true,
  imports: [CommonModule, InterviewReport],
  templateUrl: './company-dashboard.html',
  styleUrl: './company-dashboard.scss',
})
export class CompanyDashboard implements OnInit {
  private analysisService = inject(Analysis);
  private router = inject(Router);

  activeTab = signal<'candidates' | 'ranking' | 'global'>('candidates');

  // Data signals
  candidates = signal<CandidateInfo[]>([]);
  ranking = signal<RankedCandidate[]>([]);
  globalReport = signal<GlobalReport | null>(null);

  // UI state
  loading = signal(false);
  selectedReport = signal<number | null>(null);
  showReportModal = signal(false);

  ngOnInit() {
    this.loadCandidates();
  }

  setTab(tab: 'candidates' | 'ranking' | 'global') {
    this.activeTab.set(tab);

    if (tab === 'ranking' && this.ranking().length === 0) {
      this.loadRanking();
    } else if (tab === 'global' && !this.globalReport()) {
      this.loadGlobalReport();
    }
  }

  loadCandidates() {
    this.loading.set(true);
    this.analysisService.getCandidates().subscribe({
      next: (data) => {
        this.candidates.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading candidates:', err);
        this.loading.set(false);
      },
    });
  }

  loadRanking() {
    this.loading.set(true);
    this.analysisService.getRanking().subscribe({
      next: (data) => {
        this.ranking.set(data.ranking);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading ranking:', err);
        this.loading.set(false);
      },
    });
  }

  loadGlobalReport() {
    this.loading.set(true);
    this.analysisService.getGlobalReport().subscribe({
      next: (data) => {
        this.globalReport.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading global report:', err);
        this.loading.set(false);
      },
    });
  }

  viewReport(sessionId: number) {
    this.selectedReport.set(sessionId);
    this.showReportModal.set(true);
  }

  closeReportModal() {
    this.showReportModal.set(false);
    this.selectedReport.set(null);
  }

  getStatusBadgeClass(status: string): string {
    const classes: Record<string, string> = {
      pending: 'badge-pending',
      active: 'badge-active',
      completed: 'badge-completed',
      abandoned: 'badge-abandoned',
    };
    return classes[status] || '';
  }

  getScoreBadgeClass(category: string): string {
    const classes: Record<string, string> = {
      Excellent: 'score-excellent',
      Good: 'score-good',
      Fair: 'score-fair',
      Poor: 'score-poor',
    };
    return classes[category] || '';
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}
