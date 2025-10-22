import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@environment';

export interface ChatStartResponse {
  session_id: string;
  message: string;
}

export interface ChatMessageRequest {
  session_id: string;
  text: string;
}

export interface ChatMessageResponse {
  message: string;
  turns?: number;
}

@Injectable({
  providedIn: 'root',
})
export class Chat {
  private http = inject(HttpClient);
  private base = `${environment.apiBase}/ai`;

  startSession(initialPrompt: string, model: string = 'llama3.2'): Observable<ChatStartResponse> {
    return this.http.post<ChatStartResponse>(`${this.base}/chat/start`, {
      system: initialPrompt,
      model: model,
    });
  }

  sendMessage(
    sessionId: string,
    text: string,
    model: string = 'llama3.2',
  ): Observable<ChatMessageResponse> {
    const req: ChatMessageRequest & { model: string } = {
      session_id: sessionId,
      text: text,
      model: model,
    };
    return this.http.post<ChatMessageResponse>(`${this.base}/chat/message`, req);
  }
}
