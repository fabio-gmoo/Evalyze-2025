import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);

  // ✅ Permiso one-shot justo tras login para evitar condiciones de carrera
  try {
    const just = sessionStorage.getItem('justLoggedIn');
    if (just === '1') {
      sessionStorage.removeItem('justLoggedIn');
      return true;
    }
  } catch {}

  const token =
    (typeof localStorage !== 'undefined' && localStorage.getItem('token')) ||
    (typeof sessionStorage !== 'undefined' && sessionStorage.getItem('token'));

  // Si no hay token en storage, mira cookie httpOnly
  const hasCookie =
    typeof document !== 'undefined' && /\b(token|sid|session|auth)=/.test(document.cookie || '');

  if (token || hasCookie) return true;

  return router.createUrlTree(['/auth']);
};
