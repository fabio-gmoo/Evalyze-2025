export interface RegisterCompanyDto {
  email: string;
  password: string;
  confirm: string;
  company_name: string;
}

export interface RegisterCandidateDto {
  email: string;
  password: string;
  confirm: string;
  full_name: string;
}
