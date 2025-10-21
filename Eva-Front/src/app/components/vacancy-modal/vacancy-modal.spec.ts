import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VacancyModal } from './vacancy-modal';

describe('VacancyModal', () => {
  let component: VacancyModal;
  let fixture: ComponentFixture<VacancyModal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VacancyModal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VacancyModal);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
