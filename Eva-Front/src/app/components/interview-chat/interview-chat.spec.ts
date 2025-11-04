import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InterviewChat } from './interview-chat';

describe('InterviewChat', () => {
  let component: InterviewChat;
  let fixture: ComponentFixture<InterviewChat>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InterviewChat]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InterviewChat);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
