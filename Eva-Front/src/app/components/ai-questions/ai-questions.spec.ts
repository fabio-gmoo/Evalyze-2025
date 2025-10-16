import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AiQuestions } from './ai-questions';

describe('AiQuestions', () => {
  let component: AiQuestions;
  let fixture: ComponentFixture<AiQuestions>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiQuestions]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AiQuestions);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
