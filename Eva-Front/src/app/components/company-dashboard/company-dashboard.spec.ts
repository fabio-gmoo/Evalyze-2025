import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CompanyDashboards } from './company-dashboards';

describe('CompanyDashboards', () => {
  let component: CompanyDashboards;
  let fixture: ComponentFixture<CompanyDashboards>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CompanyDashboards]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CompanyDashboards);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
