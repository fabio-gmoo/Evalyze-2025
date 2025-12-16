export const environment = {
  production: false,
  // En local, todo apunta al mismo sitio (el proxy o tu backend local)
  apiUrl: 'http://localhost:8000/api',
  interviewUrl: 'http://localhost:8000/api',
  aiUrl: 'http://localhost:8000/api',
} as const;
