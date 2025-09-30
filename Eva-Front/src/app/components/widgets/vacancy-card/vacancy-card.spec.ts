import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VacancyCard } from './vacancy-card';

describe('VacancyCard', () => {
  let component: VacancyCard;
  let fixture: ComponentFixture<VacancyCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VacancyCard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VacancyCard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
