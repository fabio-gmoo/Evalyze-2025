// Eva-Front/src/app/services/interview.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '@environment';

export interface InterviewQuestion {
  id: string;
  question: string;
  type: 'technical' | 'behavioral' | 'situational';
  expected_keywords: string[];
  rubric: string;
  weight: number;
}

export interface InterviewData {
  vacancy: string;
  level: string;
  questions: InterviewQuestion[];
}

export interface InterviewSession {
  id: number;
  status: 'pending' | 'active' | 'completed' | 'abandoned';
  current_question_index: number;
  started_at?: string;
  completed_at?: string;
  last_activity: string;
  total_score: number;
  max_possible_score: number;
  candidate_name: string;
  vacancy_title: string;
  vacancy_id?: number;
  message_count: number;
  company_name?: string;
  analysis_report?: any;
}

export interface ChatMessage {
  id?: number;
  sender: 'candidate' | 'ai' | 'system';
  content: string;
  timestamp: string;
  question_index?: number;
  score?: number;
}

export interface StartInterviewResponse {
  session_id: number;
  ai_session_id: string;
  first_message: string;
  status: string;
}

export interface SendMessageResponse {
  message: string;
  current_question: number;
  total_questions: number;
  is_complete: boolean;
}

export interface MessagesResponse {
  session_id: number;
  status: string;
  messages: ChatMessage[];
  current_question: number;
  total_questions: number;
}

export interface GenerateInterviewConfig {
  level: string;
  n_questions: number;
}

// ADDED: Interface for the response when generating an interview
export interface GenerateInterviewResponse {
  interview: {
    id: number;
    vacancy_id: number;
    questions: InterviewQuestion[]; // Using the existing InterviewQuestion interface
  };
}

@Injectable({
  providedIn: 'root',
})
export class Interview {
  private http = inject(HttpClient);
  private sessionsUrl = `${environment.apiBase}/interview-sessions`;
  private jobsUrl = `${environment.apiBase}/jobs`;

  // Active session state
  private activeSessionSubject = new BehaviorSubject<InterviewSession | null>(null);
  activeSession$ = this.activeSessionSubject.asObservable();

  /**
   * Get candidate's active interview session
   */
  getActiveSession(): Observable<{ session: InterviewSession | null }> {
    // FIX: Usar this.sessionsUrl
    return this.http
      .get<{ session: InterviewSession | null }>(`${this.sessionsUrl}/my-active/`)
      .pipe(tap((data) => this.activeSessionSubject.next(data.session)));
  }

  /**
   * Get specific interview session
   */
  getSession(sessionId: number): Observable<InterviewSession> {
    // FIX: Usar this.sessionsUrl
    return this.http.get<InterviewSession>(`${this.sessionsUrl}/${sessionId}/`);
  }

  /**
   * Start an interview session
   */
  startSession(sessionId: number): Observable<StartInterviewResponse> {
    // FIX: Usar this.sessionsUrl
    return this.http.post<StartInterviewResponse>(`${this.sessionsUrl}/${sessionId}/start/`, {});
  }

  /**
   * Send a message in the interview
   */
  sendMessage(sessionId: number, message: string): Observable<SendMessageResponse> {
    // FIX: Usar this.sessionsUrl
    return this.http.post<SendMessageResponse>(`${this.sessionsUrl}/${sessionId}/send-message/`, {
      message,
    });
  }

  /**
   * Get all messages in a session
   */
  getMessages(sessionId: number): Observable<MessagesResponse> {
    return this.http.get<MessagesResponse>(`${this.sessionsUrl}/${sessionId}/chat-messages/`);
  }
  /**
   * Clear active session (when navigating away)
   */
  clearActiveSession(): void {
    this.activeSessionSubject.next(null);
  }

  /**
   * Check if there's an active session
   */
  hasActiveSession(): boolean {
    return this.activeSessionSubject.value !== null;
  }

  generateInterview(
    vacancyId: number,
    config: GenerateInterviewConfig,
  ): Observable<GenerateInterviewResponse> {
    // This is correct (using this.jobsUrl for vacancy action)
    return this.http.post<GenerateInterviewResponse>(
      `${this.jobsUrl}/${vacancyId}/generate-interview/`,
      config,
    );
  }
}
