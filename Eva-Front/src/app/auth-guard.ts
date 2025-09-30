import { CanActivateFn } from '@angular/router';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { TokenStorage } from '@services/token-storage';

export const authGuard: CanActivateFn = (route, state) => {
  const store = inject(TokenStorage);
  const router = inject(Router);

  // Verifica si el usuario está autenticado (es decir, si existe un token de acceso)
  if (store.access) {
    return true; // El usuario está autenticado, permite el acceso
  } else {
    // Si el usuario no está autenticado, redirige a la página de login
    router.navigate(['/auth']);
    return false; // Bloquea el acceso a la ruta
  }
};
