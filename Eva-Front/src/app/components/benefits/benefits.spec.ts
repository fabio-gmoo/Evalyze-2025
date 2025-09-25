import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Benefits } from './benefits';

describe('Benefits', () => {
  let component: Benefits;
  let fixture: ComponentFixture<Benefits>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Benefits]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Benefits);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
