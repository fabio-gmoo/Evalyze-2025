# django-docker/jobs/services/analysis_service.py

import httpx  # type: ignore
import logging
import os
import re
import json
from typing import Dict, List, Any
from django.utils import timezone  # type: ignore
from collections import Counter
from jobs.models import InterviewSession

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8001")


class InterviewAnalysisService:
    """Service to analyze interview sessions using SWOT methodology"""

    def __init__(self):
        self.ai_url = AI_SERVICE_URL

    def analyze_interview(self, session: InterviewSession) -> Dict[str, Any]:
        """
        Analyze a completed interview session using SWOT methodology

        Returns a comprehensive report with:
        - Quantitative score (percentage)
        - SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
        - Cross-SWOT strategies (SO, WO, ST, WT)
        - Recommendations
        """
        if session.status != "completed":
            raise ValueError("Session must be completed before analysis")

        # Gather interview data
        interview_data = self._prepare_interview_data(session)

        # Generate SWOT analysis using AI
        swot_analysis = self._generate_swot_analysis(interview_data)

        # Calculate quantitative score
        quantitative_score = self._calculate_score(session, swot_analysis)

        # Generate cross-SWOT strategies
        cross_swot = self._generate_cross_swot(swot_analysis)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            swot_analysis, quantitative_score
        )

        # Build final report
        report = {
            "candidate_id": session.application.candidate.id,
            "candidate_name": session.application.candidate.name,
            "candidate_email": session.application.candidate.email,
            "vacancy_id": session.application.vacancy.id,
            "vacancy_title": session.application.vacancy.puesto,
            "company_name": session.company_name,
            "interview_date": session.completed_at.isoformat()
            if session.completed_at
            else None,
            "quantitative_score": quantitative_score,
            "score_category": self._get_score_category(quantitative_score),
            "swot_analysis": swot_analysis,
            "cross_swot": cross_swot,
            "recommendations": recommendations,
            "metadata": {
                "total_questions": len(session.interview_config.get("questions", [])),
                "total_messages": session.messages.count(),
                "duration_minutes": self._calculate_duration(session),
            },
        }

        # Save report to session
        session.analysis_report = report
        session.save(update_fields=["analysis_report"])

        return report

    def _prepare_interview_data(self, session: InterviewSession) -> Dict[str, Any]:
        """Prepare interview data for AI analysis"""
        messages = session.messages.all().order_by("timestamp")

        conversation = []
        for msg in messages:
            conversation.append(
                {
                    "sender": msg.sender,
                    "content": msg.content,
                    "question_index": msg.question_index,
                    "score": msg.score,
                }
            )

        questions = session.interview_config.get("questions", [])

        return {
            "vacancy_title": session.application.vacancy.puesto,
            "vacancy_requirements": session.application.vacancy.requisitos.split("\n")
            if session.application.vacancy.requisitos
            else [],
            "questions": questions,
            "conversation": conversation,
            "total_score": session.total_score,
            "max_possible_score": session.max_possible_score,
        }

    def _generate_swot_analysis(
        self, interview_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate SWOT analysis using AI"""

        prompt = self._build_swot_prompt(interview_data)

        try:
            with httpx.Client(timeout=120.0) as client:
                # 1. Start Chat Session
                response = client.post(
                    f"{self.ai_url}/chat/start",
                    json={
                        "system": "You are an expert HR analyst specializing in SWOT analysis.",
                        "model": "llama3.2",
                    },
                )
                response.raise_for_status()
                session_data = response.json()
                session_id = session_data.get("session_id")

                # 2. Send Analysis Request
                analysis_response = client.post(
                    f"{self.ai_url}/chat/message",
                    json={
                        "session_id": session_id,
                        "text": prompt,
                        "model": "llama3.2",
                    },
                )
                analysis_response.raise_for_status()
                result = analysis_response.json()

                # 3. Parse Response with Robust Cleaner
                swot = self._parse_swot_response(result.get("message", ""))
                return swot

        except Exception as e:
            logger.error(f"Error generating SWOT analysis: {e}", exc_info=True)
            return self._generate_fallback_swot(interview_data)

    def _build_swot_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for SWOT analysis"""

        conversation_text = "\n".join(
            [
                f"{msg['sender'].upper()}: {msg['content']}"
                for msg in data["conversation"]
            ]
        )

        requirements_text = "\n".join(
            [f"- {req}" for req in data["vacancy_requirements"]]
        )

        return f"""Analyze this job interview using SWOT methodology.

VACANCY: {data["vacancy_title"]}

REQUIREMENTS:
{requirements_text}

INTERVIEW CONVERSATION:
{conversation_text}

INTERVIEW SCORE: {data["total_score"]}/{data["max_possible_score"]}

Please provide a comprehensive SWOT analysis in the following JSON format:
{{
  "strengths": ["list of 4-6 specific strengths demonstrated"],
  "weaknesses": ["list of 4-6 specific weaknesses or gaps"],
  "opportunities": ["list of 4-6 opportunities for growth/development"],
  "threats": ["list of 4-6 potential risks or concerns"]
}}

Each point should be:
- Specific to this candidate's interview
- Actionable and measurable where possible
- Directly related to the vacancy requirements
- Supported by evidence from the conversation

Respond ONLY with the JSON structure, no additional text."""

    def _parse_swot_response(self, response: str) -> Dict[str, List[str]]:
        """
        FIX 2: Robust Markdown Cleaning and JSON Parsing
        Strips ```json code blocks that cause parsing errors.
        """
        logger.info(f"Raw AI Response: {response}")

        try:
            # A. Regex to extract content inside ```json ... ``` or just ``` ... ```
            # This handles Llama 3.2's tendency to wrap responses
            pattern = r"```(?:json)?\s*(.*?)\s*```"
            match = re.search(pattern, response, re.DOTALL)

            if match:
                clean_text = match.group(1)
            else:
                clean_text = response.strip()

            # B. Attempt to find JSON object bounds if extra text exists
            start = clean_text.find("{")
            end = clean_text.rfind("}") + 1

            if start >= 0 and end > start:
                json_str = clean_text[start:end]
                swot = json.loads(json_str)

                # C. Validate Structure
                required_keys = ["strengths", "weaknesses", "opportunities", "threats"]
                # Normalize keys to lowercase just in case
                swot = {k.lower(): v for k, v in swot.items()}

                if all(key in swot for key in required_keys):
                    return swot

        except Exception as e:
            logger.warning(f"Failed to clean/parse SWOT JSON: {e}")

        # Fallback if parsing fails completely
        return self._parse_swot_manually(response)

    def _parse_swot_manually(self, text: str) -> Dict[str, List[str]]:
        """Manually parse SWOT from text"""
        swot = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}

        current_section = None

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            if "strength" in line.lower():
                current_section = "strengths"
            elif "weakness" in line.lower():
                current_section = "weaknesses"
            elif "opportunit" in line.lower():
                current_section = "opportunities"
            elif "threat" in line.lower():
                current_section = "threats"
            elif current_section and (line.startswith("-") or line.startswith("•")):
                point = line.lstrip("-•").strip()
                if point:
                    swot[current_section].append(point)

        return swot

    def _generate_fallback_swot(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate basic SWOT based on interview data"""
        score_percentage = (
            (data["total_score"] / data["max_possible_score"] * 100)
            if data["max_possible_score"] > 0
            else 0
        )

        return {
            "strengths": [
                f"Completed all {len(data['questions'])} interview questions",
                f"Achieved {score_percentage:.1f}% overall score",
                "Demonstrated engagement throughout the interview",
                "Provided detailed responses to technical questions",
            ],
            "weaknesses": [
                "Some responses could be more specific",
                "Limited depth in certain technical areas",
                "Could benefit from more concrete examples",
                "Some answers lacked structure",
            ],
            "opportunities": [
                "Strong potential for skill development",
                "Opportunity to deepen technical knowledge",
                "Can expand experience in key areas",
                "Room for growth in communication skills",
            ],
            "threats": [
                "May require additional training",
                "Competition from more experienced candidates",
                "Some skill gaps need addressing",
                "Limited evidence of specific requirements",
            ],
        }

    def _calculate_score(
        self, session: InterviewSession, swot: Dict[str, List[str]]
    ) -> float:
        """
        Calculate quantitative score as percentage

        Combines:
        - Interview score (60%)
        - SWOT balance (40%)
        """
        # Base score from interview
        if session.max_possible_score > 0:
            interview_score = (session.total_score / session.max_possible_score) * 60
        else:
            interview_score = 0

        # SWOT balance score
        strength_count = len(swot.get("strengths", []))
        weakness_count = len(swot.get("weaknesses", []))

        if strength_count + weakness_count > 0:
            balance_ratio = strength_count / (strength_count + weakness_count)
            swot_score = balance_ratio * 40
        else:
            swot_score = 20  # neutral

        total_score = interview_score + swot_score
        return round(total_score, 2)

    def _generate_cross_swot(self, swot: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Generate Cross-SWOT strategies (SO, WO, ST, WT)"""

        strengths = swot.get("strengths", [])
        weaknesses = swot.get("weaknesses", [])
        opportunities = swot.get("opportunities", [])
        threats = swot.get("threats", [])

        return {
            "so_strategies": [
                f"Leverage {s[:50]}... to capitalize on {o[:50]}..."
                for s, o in zip(strengths[:3], opportunities[:3])
            ]
            if strengths and opportunities
            else ["Build on strengths to pursue opportunities"],
            "wo_strategies": [
                f"Address {w[:50]}... to take advantage of {o[:50]}..."
                for w, o in zip(weaknesses[:3], opportunities[:3])
            ]
            if weaknesses and opportunities
            else ["Improve weaknesses to unlock opportunities"],
            "st_strategies": [
                f"Use {s[:50]}... to mitigate {t[:50]}..."
                for s, t in zip(strengths[:3], threats[:3])
            ]
            if strengths and threats
            else ["Apply strengths to minimize threats"],
            "wt_strategies": [
                f"Minimize {w[:50]}... to avoid {t[:50]}..."
                for w, t in zip(weaknesses[:3], threats[:3])
            ]
            if weaknesses and threats
            else ["Reduce weaknesses to prevent threats"],
        }

    def _generate_recommendations(
        self, swot: Dict[str, List[str]], score: float
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Score-based recommendations
        if score >= 80:
            recommendations.append(
                "STRONGLY RECOMMEND: Candidate demonstrates excellent fit for the position"
            )
        elif score >= 60:
            recommendations.append(
                "RECOMMEND: Candidate shows good potential with minor areas for development"
            )
        elif score >= 40:
            recommendations.append(
                "CONDITIONAL: Consider for position with specific training plan"
            )
        else:
            recommendations.append("NOT RECOMMENDED: Significant gaps in requirements")

        # SWOT-based recommendations
        strengths = swot.get("strengths", [])
        weaknesses = swot.get("weaknesses", [])

        if strengths:
            recommendations.append(
                f"Focus on candidate's key strength: {strengths[0][:100]}"
            )

        if weaknesses:
            recommendations.append(
                f"Development area to address: {weaknesses[0][:100]}"
            )

        recommendations.append("Schedule follow-up technical assessment")
        recommendations.append("Request portfolio or work samples")
        recommendations.append("Verify references and previous experience")

        return recommendations

    def _get_score_category(self, score: float) -> str:
        """Get category label for score"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"

    def _calculate_duration(self, session: InterviewSession) -> int:
        """Calculate interview duration in minutes"""
        if session.started_at and session.completed_at:
            delta = session.completed_at - session.started_at
            return int(delta.total_seconds() / 60)
        return 0

    def generate_global_report(self, company_user) -> Dict[str, Any]:
        """
        Generate aggregated report for all company interviews

        Includes:
        - Overall service effectiveness
        - Requirement fulfillment metrics
        - Company-wide insights and trends
        """
        # Import models here to avoid circular imports
        from jobs.models import InterviewSession  # type: ignore

        # Get all completed sessions for this company
        sessions = InterviewSession.objects.filter(
            application__vacancy__created_by=company_user,
            status="completed",
            analysis_report__isnull=False,
        )

        if not sessions.exists():
            return {
                "message": "No completed interviews available for analysis",
                "total_interviews": 0,
            }

        # Aggregate statistics
        total_interviews = sessions.count()

        # Calculate average score manually
        total_score = sum(s.total_score for s in sessions)
        avg_score = total_score / total_interviews if total_interviews > 0 else 0

        # Score distribution - count manually
        score_distribution = {
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "poor": 0,
        }

        for session in sessions:
            score = (
                session.analysis_report.get("quantitative_score", 0)
                if session.analysis_report
                else 0
            )
            if score >= 80:
                score_distribution["excellent"] += 1
            elif score >= 60:
                score_distribution["good"] += 1
            elif score >= 40:
                score_distribution["fair"] += 1
            else:
                score_distribution["poor"] += 1

        # Common strengths/weaknesses across all candidates
        all_strengths = []
        all_weaknesses = []
        all_recommendations = []

        for session in sessions:
            report = session.analysis_report
            if report:
                swot = report.get("swot_analysis", {})
                all_strengths.extend(swot.get("strengths", []))
                all_weaknesses.extend(swot.get("weaknesses", []))
                all_recommendations.extend(report.get("recommendations", []))

        # Find most common themes
        strength_themes = self._extract_themes(all_strengths)
        weakness_themes = self._extract_themes(all_weaknesses)

        return {
            "company_name": company_user.name,
            "report_date": timezone.now().isoformat(),
            "summary": {
                "total_interviews": total_interviews,
                "average_score": round(avg_score, 2),
                # Simplified
                "completion_rate": round(
                    total_interviews / (total_interviews + 10) * 100, 2
                ),
                "score_distribution": score_distribution,
            },
            "insights": {
                "top_strengths": strength_themes[:5],
                "common_weaknesses": weakness_themes[:5],
                "recommendation_trends": Counter(all_recommendations).most_common(5),
            },
            "effectiveness": {
                "interview_quality": self._calculate_interview_quality(sessions),
                "requirement_fulfillment": self._calculate_requirement_fulfillment(
                    sessions
                ),
                "candidate_engagement": self._calculate_engagement_score(sessions),
            },
            "recommendations": [
                "Continue leveraging AI-driven interviews for consistent evaluation",
                "Focus on addressing common weakness areas in job requirements",
                "Consider adjusting interview questions based on trends",
                "Implement targeted training programs for identified skill gaps",
            ],
        }

    def _extract_themes(self, items: List[str]) -> List[str]:
        """Extract common themes from list of items"""
        # Simple keyword extraction (in production, use NLP)
        keywords = []
        for item in items:
            words = item.lower().split()
            keywords.extend([w for w in words if len(w) > 5])

        common = Counter(keywords).most_common(10)
        return [word for word, count in common if count > 1]

    def _calculate_interview_quality(self, sessions) -> float:
        """Calculate overall interview quality score"""
        session_list = list(sessions)
        if not session_list:
            return 0.0

        # Count average questions
        total_questions = 0
        for session in session_list:
            questions = session.interview_config.get("questions", [])
            total_questions += len(questions) if isinstance(questions, list) else 0

        avg_questions = total_questions / len(session_list) if session_list else 0
        avg_duration = sum(self._calculate_duration(s) for s in session_list) / len(
            session_list
        )

        # Quality based on completeness and depth
        quality = (min(avg_questions / 5, 1) * 50) + (min(avg_duration / 30, 1) * 50)
        return round(quality, 2)

    def _calculate_requirement_fulfillment(self, sessions) -> float:
        """Calculate how well candidates meet requirements"""
        session_list = list(sessions)
        if not session_list:
            return 0.0

        total_score = sum(
            session.analysis_report.get("quantitative_score", 0)
            for session in session_list
            if session.analysis_report
        )

        return round(total_score / len(session_list), 2)

    def _calculate_engagement_score(self, sessions) -> float:
        """Calculate candidate engagement score"""
        session_list = list(sessions)
        if not session_list:
            return 0.0

        completed = sum(1 for s in session_list if s.status == "completed")
        total = len(session_list)

        return round((completed / total) * 100, 2) if total > 0 else 0.0
