export const environment = {
  production: true,
  // Backend Principal (Auth, Usuarios, Vacantes/Jobs)
  apiUrl: 'https://evalyze-web-service-production.up.railway.app',

  // Servicio de Entrevistas y Análisis
  interviewUrl: 'https://evalyze-interview-production.up.railway.app',

  // Servicio de Inteligencia Artificial (Chat)
  aiUrl: 'https://evalyze-ai-production.up.railway.app',
} as const;
