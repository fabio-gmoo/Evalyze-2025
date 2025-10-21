export type UserRole = 'candidate' | 'company';

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface Me {
  id: number;
  email: string;
  role: UserRole;
  name: string;
}

export interface LoginResponse extends TokenPair {
  user: Me;
}
