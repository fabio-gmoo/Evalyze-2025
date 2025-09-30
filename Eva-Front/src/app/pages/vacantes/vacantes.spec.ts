import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Vacantes } from './vacantes';

describe('Vacantes', () => {
  let component: Vacantes;
  let fixture: ComponentFixture<Vacantes>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Vacantes]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Vacantes);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
