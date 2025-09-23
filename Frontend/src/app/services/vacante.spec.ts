import { TestBed } from '@angular/core/testing';

import { Vacante } from './vacante';

describe('Vacante', () => {
  let service: Vacante;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Vacante);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
