import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VacancyTabs } from './vacancy-tabs';

describe('VacancyTabs', () => {
  let component: VacancyTabs;
  let fixture: ComponentFixture<VacancyTabs>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VacancyTabs]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VacancyTabs);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
