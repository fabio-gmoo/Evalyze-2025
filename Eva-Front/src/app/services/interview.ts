import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@environment';

export interface InterviewQuestion {
  id: string;
  question: string;
  type: 'technical' | 'behavioral' | 'situational';
  expected_keywords: string[];
  rubric: string;
  weight: number;
}

// Renamed the main interview structure interface
export interface InterviewData {
  vacancy: string;
  level: string;
  questions: InterviewQuestion[];
}

export interface ChatInitiationStatus {
  chat_status: string;
  started_chats: number[];
}

// Corrected the response interface to explicitly use the data structure
export interface GenerateInterviewResponse {
  interview: InterviewData; // <-- Using InterviewData here
  vacancy: any;
  chat_status?: string;
  started_chats?: number[];
}

export interface GenerateInterviewRequest {
  level?: 'junior' | 'intermedio' | 'senior';
  n_questions?: number;
}

@Injectable({
  providedIn: 'root',
})
export class Interview {
  private http = inject(HttpClient);
  private base = `${environment.apiBase}/jobs`;

  generateInterview(
    vacancyId: number,
    request: GenerateInterviewRequest = {},
  ): Observable<GenerateInterviewResponse> {
    return this.http.post<GenerateInterviewResponse>(
      `${this.base}/${vacancyId}/generate-interview/`,
      {
        level: request.level || 'intermedio',
        n_questions: request.n_questions || 4,
      },
    );
  }
}
