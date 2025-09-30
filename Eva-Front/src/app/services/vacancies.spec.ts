import { TestBed } from '@angular/core/testing';

import { Vacancies } from './vacancies';

describe('Vacancies', () => {
  let service: Vacancies;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Vacancies);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
