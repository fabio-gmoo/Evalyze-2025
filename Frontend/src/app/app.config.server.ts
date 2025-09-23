import { ApplicationConfig } from '@angular/core';
import { provideServerRendering } from '@angular/platform-server';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { serverRoutes } from './app.routes.server';

export const config: ApplicationConfig = {
  providers: [
    provideServerRendering(),
    provideRouter(serverRoutes),
    provideHttpClient(),
  ],
};
