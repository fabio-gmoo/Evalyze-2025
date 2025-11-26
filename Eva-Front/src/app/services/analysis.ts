import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@environment';

export interface SWOTAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface CrossSWOT {
  so_strategies: string[];
  wo_strategies: string[];
  st_strategies: string[];
  wt_strategies: string[];
}

export interface InterviewReport {
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  vacancy_id: number;
  vacancy_title: string;
  company_name: string;
  interview_date: string;
  quantitative_score: number;
  score_category: string;
  swot_analysis: SWOTAnalysis;
  cross_swot: CrossSWOT;
  recommendations: string[];
  metadata: {
    total_questions: number;
    total_messages: number;
    duration_minutes: number;
  };
}

export interface CandidateInfo {
  id: number;
  name: string;
  email: string;
  vacancy_title: string;
  applied_at: string;
  status: string;
  interview: {
    session_id: number;
    status: string;
    completed_at: string | null;
    has_analysis: boolean;
    score: number | null;
  } | null;
}

export interface RankedCandidate {
  rank: number;
  candidate: {
    id: number;
    name: string;
    email: string;
  };
  vacancy_title: string;
  score: number;
  score_category: string;
  completed_at: string;
  session_id: number;
  summary: {
    strengths_count: number;
    weaknesses_count: number;
    top_recommendation: string;
  };
}

export interface GlobalReport {
  company_name: string;
  report_date: string;
  summary: {
    total_interviews: number;
    average_score: number;
    completion_rate: number;
    score_distribution: {
      excellent: number;
      good: number;
      fair: number;
      poor: number;
    };
  };
  insights: {
    top_strengths: string[];
    common_weaknesses: string[];
    recommendation_trends: Array<[string, number]>;
  };
  effectiveness: {
    interview_quality: number;
    requirement_fulfillment: number;
    candidate_engagement: number;
  };
  recommendations: string[];
}

@Injectable({
  providedIn: 'root',
})
export class Analysis {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiBase}/interview-sessions`;
  finalizeInterview(sessionId: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/${sessionId}/finalize/`, {});
  }

  getReport(sessionId: number): Observable<InterviewReport> {
    return this.http.get<InterviewReport>(`${this.baseUrl}/${sessionId}/report/`);
  }

  analyzeInterview(sessionId: number): Observable<InterviewReport> {
    return this.http.post<InterviewReport>(`${this.baseUrl}/${sessionId}/analyze/`, {});
  }

  getCandidates(): Observable<CandidateInfo[]> {
    return this.http.get<CandidateInfo[]>(`${this.baseUrl}/candidates/`);
  }

  getRanking(): Observable<{ total_candidates: number; ranking: RankedCandidate[] }> {
    return this.http.get<{ total_candidates: number; ranking: RankedCandidate[] }>(
      `${this.baseUrl}/ranking/`,
    );
  }

  getGlobalReport(): Observable<GlobalReport> {
    return this.http.get<GlobalReport>(`${this.baseUrl}/global-report/`);
  }
}
