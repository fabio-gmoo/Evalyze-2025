export interface LoginDto {
  email: string;
  password: string;
  role: 'company' | 'candidate';
  remember?: boolean;
}
