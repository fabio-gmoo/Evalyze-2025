import { HttpInterceptorFn, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { inject } from '@angular/core';
import { Auth } from '@services/auth';
import { TokenStorage } from '@services/token-storage';
import { catchError, switchMap, tap, take, filter } from 'rxjs/operators';
import { throwError, ReplaySubject } from 'rxjs';

let refreshInFlight = false;
const refreshedAccess$ = new ReplaySubject<string>(1);

export const authTokenInterceptor: HttpInterceptorFn = (req, next) => {
  const store = inject(TokenStorage);
  const auth = inject(Auth);

  const isAuthPath = /\/auth\/(login|refresh)\//.test(req.url);

  // Adjunta Bearer solo si tenemos access y NO es login/refresh
  const withAuth =
    store.access && !isAuthPath
      ? req.clone({ setHeaders: { Authorization: `Bearer ${store.access}` } })
      : req;

  return next(withAuth).pipe(
    catchError((err: HttpErrorResponse) => {
      // Si no es 401, o es login/refresh, no intentamos refrescar
      if (err.status !== 401 || isAuthPath) {
        return throwError(() => err);
      }

      // Si no hay refresh token → cerrar sesión
      if (!store.refresh) {
        auth.logout();
        return throwError(() => err);
      }

      // Si nadie está refrescando, inicia refresh y comparte resultado
      if (!refreshInFlight) {
        refreshInFlight = true;

        return auth.refresh().pipe(
          tap((newAccess) => {
            refreshInFlight = false;
            refreshedAccess$.next(newAccess);
          }),
          // Reintenta la request ORIGINAL con el token nuevo
          switchMap((newAccess) => {
            const retryReq = req.clone({ setHeaders: { Authorization: `Bearer ${newAccess}` } });
            return next(retryReq);
          }),
          catchError((refreshErr) => {
            refreshInFlight = false;
            auth.logout();
            return throwError(() => refreshErr);
          }),
        );
      }

      // Si ya hay un refresh en curso, espera a que emita y reintenta
      return refreshedAccess$.pipe(
        take(1),
        filter((t) => !!t),
        switchMap((newAccess) => {
          const retryReq = req.clone({ setHeaders: { Authorization: `Bearer ${newAccess}` } });
          return next(retryReq);
        }),
      );
    }),
  );
};
