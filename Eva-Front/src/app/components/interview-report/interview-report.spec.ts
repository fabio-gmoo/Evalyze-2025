import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InterviewReport } from './interview-report';

describe('InterviewReport', () => {
  let component: InterviewReport;
  let fixture: ComponentFixture<InterviewReport>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InterviewReport]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InterviewReport);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
