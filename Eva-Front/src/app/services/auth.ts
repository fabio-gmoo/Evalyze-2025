import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { environment } from '@environment';
// import { environment } from '@environments/environment';
import { RegisterCandidateDto, RegisterCompanyDto } from '@interfaces/register-dto';
import { LoginDto } from '@interfaces/login-dto';
import { LoginResponse, Me, TokenPair } from '@interfaces/token-types-dto';
import { TokenStorage } from '@services/token-storage';
import { Observable, throwError } from 'rxjs';
import { catchError, tap, map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  private http = inject(HttpClient);
  private store = inject(TokenStorage);
  private base = environment.apiBase;

  /** --- Helpers públicos --- */
  me$ = this.store.me$;

  isAuthenticated(): boolean {
    return !!this.store.access;
  }

  getAccessToken(): string | null {
    return this.store.access;
  }

  /** --- Endpoints --- */
  registerCandidate(dto: RegisterCandidateDto): Observable<Me> {
    return this.http
      .post<Me>(`${this.base}/auth/register/candidate/`, dto)
      .pipe(catchError(this._handle));
  }

  registerCompany(dto: RegisterCompanyDto): Observable<Me> {
    return this.http
      .post<Me>(`${this.base}/auth/register/company/`, dto)
      .pipe(catchError(this._handle));
  }

  login(dto: LoginDto): Observable<Me> {
    return this.http.post<LoginResponse>(`${this.base}/auth/login/`, dto).pipe(
      tap((res) => {
        this.store.setTokens({ access: res.access, refresh: res.refresh });
        this.store.setMe(res.user);
      }),
      map((res) => res.user),
      catchError(this._handle),
    );
  }

  refresh(): Observable<string> {
    const refresh = this.store.refresh;
    if (!refresh) return throwError(() => new Error('No refresh token'));

    return this.http.post<TokenPair>(`${this.base}/auth/refresh/`, { refresh }).pipe(
      tap((tp) => this.store.setTokens(tp)),
      map((tp) => tp.access),
      catchError(this._handle),
    );
  }

  me(): Observable<Me> {
    return this.http.get<Me>(`${this.base}/auth/me/`).pipe(
      tap((me) => this.store.setMe(me)),
      catchError(this._handle),
    );
  }

  logout() {
    this.store.clear();
  }

  /** --- Error handler --- */
  private _handle(err: unknown) {
    const e = err as HttpErrorResponse;
    // Opcional: mapear errores del backend a mensajes amigables
    return throwError(() => e);
  }
}
