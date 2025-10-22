import { Component, Input, Output, EventEmitter, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VacanteUI } from '@interfaces/vacante-model';
import { VacancyTabs } from '@components/vacancy-tabs/vacancy-tabs';
import { Tab, FormData } from '@interfaces/vacante-model';
import { Interview } from '@services/interview';
import { InterviewQuestion, GenerateInterviewResponse } from '@services/interview';
import { ChatModal } from '@components/chat-modal/chat-modal';

@Component({
  selector: 'app-vacancy-details-modal',
  imports: [CommonModule, VacancyTabs, ChatModal],
  templateUrl: './vacancy-details-modal.html',
  styleUrl: './vacancy-details-modal.scss',
})
export class VacancyDetailsModal implements OnInit {
  private interviewService = inject(Interview);
  @Input() vacancy!: VacanteUI;
  @Input() viewMode: 'company' | 'candidate' = 'company';
  @Output() close = new EventEmitter<void>();
  @Output() apply = new EventEmitter<VacanteUI>();
  @Output() edit = new EventEmitter<VacanteUI>();
  @Output() generateInterview = new EventEmitter<number>();

  isChatModalOpen = false;
  activeInterviewQuestions: InterviewQuestion[] | null = null;

  activeTab = 'detalles';

  get tabs(): Tab[] {
    const baseTabs: Tab[] = [{ id: 'detalles', label: 'Detalles' }];

    if (this.viewMode === 'company') {
      baseTabs.push({
        id: 'candidatos',
        label: `Candidatos (${this.vacancy.candidatos || 0})`,
      });
    }

    return baseTabs;
  }

  ngOnInit() {
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
  }

  ngOnDestroy() {
    // Restore body scroll
    document.body.style.overflow = '';
  }

  onClose() {
    this.close.emit();
  }

  onApply() {
    this.apply.emit(this.vacancy);
  }

  onEdit() {
    this.edit.emit(this.vacancy);
  }

  setActiveTab(tab: string) {
    this.activeTab = tab;
  }

  onBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      this.onClose();
    }
  }

  onGenerateInterview() {
    if (!this.vacancy.id) return;

    this.generateInterview.emit(this.vacancy.id);
  }

  openChat(vacancyId: number | undefined) {
    if (!vacancyId) {
      console.error('Cannot open chat: Vacancy ID is missing.');
      return;
    }

    this.interviewService
      .generateInterview(vacancyId)
      .subscribe((response: GenerateInterviewResponse) => {
        this.activeInterviewQuestions = response.interview.questions;
        this.isChatModalOpen = true;
      });
  }
}
