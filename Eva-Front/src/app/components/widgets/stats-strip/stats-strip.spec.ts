import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StatsStrip } from './stats-strip';

describe('StatsStrip', () => {
  let component: StatsStrip;
  let fixture: ComponentFixture<StatsStrip>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatsStrip]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StatsStrip);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
