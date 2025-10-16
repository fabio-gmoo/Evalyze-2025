import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VacancyHeader } from './vacancy-header';

describe('VacancyHeader', () => {
  let component: VacancyHeader;
  let fixture: ComponentFixture<VacancyHeader>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VacancyHeader]
    })
    .compileComponents();

    fixture = TestBed.createComponent(VacancyHeader);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
