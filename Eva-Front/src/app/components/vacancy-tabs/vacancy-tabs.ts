import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Tab } from '@interfaces/vacante-model';

@Component({
  selector: 'app-vacancy-tabs',
  imports: [CommonModule],
  templateUrl: './vacancy-tabs.html',
  styleUrl: './vacancy-tabs.scss',
})
export class VacancyTabs {
  @Input() tabs: Tab[] = [];
  @Input() activeTab: string = '';
  @Output() tabChange = new EventEmitter<string>();

  onTabClick(tabId: string): void {
    this.tabChange.emit(tabId);
  }
}
