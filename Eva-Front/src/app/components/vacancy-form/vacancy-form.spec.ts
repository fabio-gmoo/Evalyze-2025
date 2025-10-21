import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VacancyForm } from './vacancy-form';

describe('VacancyForm', () => {
  let component: VacancyForm;
  let fixture: ComponentFixture<VacancyForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VacancyForm]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VacancyForm);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
