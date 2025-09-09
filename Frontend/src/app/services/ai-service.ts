import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../enviroments/enviroment.development';

export interface Health {
  status: string;
  model?: string;
}
export interface ChatResponse {
  reply: string;
}

@Injectable({ providedIn: 'root' })
export class AiService {
  private http = inject(HttpClient);
  private base = environment.apiBase;

  health() {
    return this.http.get<Health>(`${this.base}/health`);
  }

  demoChat(message: string, sessionId = 'front-demo-1', demoKey = 'evalyze-demo-123') {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      'X-Demo-Key': demoKey,
    });
    return this.http.post<ChatResponse>(
      `${this.base}/ai/demo-chat`,
      { session_id: sessionId, message },
      { headers }
    );
  }

  chat(message: string, sessionId = 'front-dev-1', jwt?: string) {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json',
      ...(jwt ? { Authorization: `Bearer ${jwt}` } : {}),
    });
    return this.http.post<ChatResponse>(
      `${this.base}/ai/chat`,
      { session_id: sessionId, message },
      { headers }
    );
  }
}
