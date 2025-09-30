import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Me, TokenPair } from '@interfaces/token-types-dto';

@Injectable({
  providedIn: 'root',
})
export class TokenStorage {
  private accessSubject = new BehaviorSubject<string | null>(null);
  private refreshSubject = new BehaviorSubject<string | null>(null);
  private userSubject = new BehaviorSubject<Me | null>(null);

  access$ = this.accessSubject.asObservable();
  refresh$ = this.refreshSubject.asObservable();
  me$ = this.userSubject.asObservable();

  get access() {
    return this.accessSubject.value;
  }

  set access(token: string | null) {
    this.accessSubject.next(token);
  }

  get refresh() {
    return this.refreshSubject.value;
  }

  set refresh(token: string | null) {
    this.refreshSubject.next(token);
  }

  get me() {
    return this.userSubject.value;
  }

  setMe(user: Me) {
    this.userSubject.next(user); // ✅ Cambiado de meSubject a userSubject
  }

  clear() {
    this.accessSubject.next(null);
    this.refreshSubject.next(null);
    this.userSubject.next(null);
  }

  setTokens(tokens: { access: string; refresh: string }) {
    this.access = tokens.access;
    this.refresh = tokens.refresh;
  }
}
