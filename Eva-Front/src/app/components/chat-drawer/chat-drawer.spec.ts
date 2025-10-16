import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ChatDrawer } from './chat-drawer';

describe('ChatDrawer', () => {
  let component: ChatDrawer;
  let fixture: ComponentFixture<ChatDrawer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatDrawer]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ChatDrawer);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
