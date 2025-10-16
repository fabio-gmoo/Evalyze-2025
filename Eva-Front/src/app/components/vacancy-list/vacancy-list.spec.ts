import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VacancyList } from './vacancy-list';

describe('VacancyList', () => {
  let component: VacancyList;
  let fixture: ComponentFixture<VacancyList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VacancyList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VacancyList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
