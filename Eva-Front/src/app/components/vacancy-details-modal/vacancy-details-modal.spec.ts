import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VacancyDetailsModal } from './vacancy-details-modal';

describe('VacancyDetailsModal', () => {
  let component: VacancyDetailsModal;
  let fixture: ComponentFixture<VacancyDetailsModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VacancyDetailsModal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VacancyDetailsModal);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
