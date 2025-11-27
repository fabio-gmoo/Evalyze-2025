# django-docker/jobs/views_interview.py

from rest_framework import viewsets, status  # type: ignore
from rest_framework.decorators import action  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.permissions import IsAuthenticated  # type: ignore
from .models import InterviewSession, ChatMessage, Application
from .services.interview_service import InterviewService  # type: ignore
from .services.analysis_service import InterviewAnalysisService  # type: ignore
from .serializers import InterviewSessionSerializer  # type: ignore
import logging

logger = logging.getLogger(__name__)


class InterviewSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing interview sessions
    """

    serializer_class = InterviewSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "candidate":
            return InterviewSession.objects.filter(application__candidate=user)

        elif user.role == "company":
            # Companies can see sessions for their vacancies
            return InterviewSession.objects.filter(
                application__vacancy__created_by=user
            )

        return InterviewSession.objects.none()

    @action(detail=True, methods=["post"], url_path="start")
    def start_session(self, request, pk=None):
        """
        Start an interview session
        Only the candidate can start their own session
        """
        session = self.get_object()

        # Verify candidate ownership
        if session.application.candidate != request.user:
            return Response(
                {"detail": "No tienes permiso para iniciar esta sesión"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if already started
        if session.status != "pending":
            return Response(
                {"detail": "Esta sesión ya fue iniciada"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = InterviewService()
            result = service.start_interview(session)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error starting session: {e}", exc_info=True)
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        """
        Send a message in the interview chat
        """
        session = self.get_object()

        # Verify candidate ownership
        if session.application.candidate != request.user:
            return Response(
                {"detail": "No tienes permiso para enviar mensajes en esta sesión"},
                status=status.HTTP_403_FORBIDDEN,
            )

        message = request.data.get("message", "").strip()
        if not message:
            return Response(
                {"detail": "El mensaje no puede estar vacío"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = InterviewService()
            result = service.send_message(session, message)

            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return Response(
                {"detail": "Error al enviar el mensaje"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # <-- ESTE DEBE ESTAR DEFINIDO
    @action(detail=True, methods=["get"], url_path="chat-messages")
    def get_messages(self, request, pk=None):
        """
        Get all messages in a session
        """
        session = self.get_object()

        service = InterviewService()
        messages = service.get_session_history(session)

        return Response(
            {
                "session_id": session.id,
                "status": session.status,
                "messages": messages,
                "current_question": session.current_question_index,
                "total_questions": len(session.interview_config.get("questions", [])),
            }
        )

    @action(detail=False, methods=["get"], url_path="my-active")
    def my_active_session(self, request):
        """
        Get candidate's active session (if any)
        """
        try:
            if request.user.role != "candidate":
                return Response(
                    {"detail": "Solo candidatos pueden acceder"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Try to get active session
            active_session = (
                InterviewSession.objects.filter(
                    application__candidate=request.user,
                    status__in=["pending", "active"],
                )
                .select_related("application__candidate", "application__vacancy")
                .order_by("-started_at", "-id")
                .first()
            )

            if not active_session:
                return Response({"session": None}, status=status.HTTP_200_OK)

            serializer = self.get_serializer(active_session)
            return Response({"session": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in my_active_session: {e}", exc_info=True)
            # Return empty session instead of 500 error
            return Response(
                {"session": None, "error": "Unable to fetch session"},
                status=status.HTTP_200_OK,
            )

    @action(detail=True, methods=["post"], url_path="finalize")
    def finalize_interview(self, request, pk=None):
        """
        Finalize interview and trigger SWOT analysis
        Candidate-only endpoint
        """
        session = self.get_object()

        # Verify candidate ownership
        if session.application.candidate != request.user:
            return Response(
                {"detail": "No tienes permiso para finalizar esta sesión"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if already completed
        if session.status != "active":
            return Response(
                {"detail": "Esta sesión no está activa"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Mark as completed
            session.complete_session()

            # Trigger analysis
            analysis_service = InterviewAnalysisService()
            report = analysis_service.analyze_interview(session)

            logger.info(f"Interview {session.id} finalized and analyzed")

            return Response(
                {
                    "message": "Entrevista finalizada exitosamente",
                    "status": "completed",
                    "analysis_available": True,
                    "score": report.get("quantitative_score"),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error finalizing interview: {e}", exc_info=True)
            return Response(
                {"detail": f"Error al finalizar entrevista: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="report")
    def get_report(self, request, pk=None):
        """
        Get interview analysis report
        Accessible by candidate (own) or company (their vacancies)
        """
        session = self.get_object()

        # Check if analysis exists
        if not session.has_analysis():
            return Response(
                {"detail": "Análisis no disponible aún"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(session.analysis_report, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze_interview(self, request, pk=None):
        """
        Manually trigger analysis (company-only)
        Useful for re-analysis or if auto-analysis failed
        """
        session = self.get_object()

        # Verify company ownership
        if session.application.vacancy.created_by != request.user:
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if session.status != "completed":
            return Response(
                {"detail": "La sesión debe estar completada"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            analysis_service = InterviewAnalysisService()
            report = analysis_service.analyze_interview(session)

            return Response(report, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error analyzing interview: {e}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="candidates")
    def list_candidates(self, request):
        """
        List all candidates with their interview status (company-only)
        """
        if request.user.role != "company":
            return Response(
                {"detail": "Solo empresas"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get all applications for company's vacancies
        applications = Application.objects.filter(
            vacancy__created_by=request.user
        ).select_related("candidate", "vacancy", "interview_session")

        candidates_data = []
        for app in applications:
            session = getattr(app, "interview_session", None)

            candidate_info = {
                "id": app.candidate.id,
                "name": app.candidate.name,
                "email": app.candidate.email,
                "vacancy_title": app.vacancy.puesto,
                "applied_at": app.applied_at.isoformat(),
                "status": app.status,
                "interview": None,
            }

            if session:
                candidate_info["interview"] = {
                    "session_id": session.id,
                    "status": session.status,
                    "completed_at": session.completed_at.isoformat()
                    if session.completed_at
                    else None,
                    "has_analysis": session.has_analysis(),
                    "score": session.get_score_percentage()
                    if session.has_analysis()
                    else None,
                }

            candidates_data.append(candidate_info)

        return Response(candidates_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="ranking")
    def get_ranking(self, request):
        """
        Get ranked candidates based on interview scores (company-only)
        """
        if request.user.role != "company":
            return Response(
                {"detail": "Solo empresas"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get all completed sessions with analysis
        sessions = InterviewSession.objects.filter(
            application__vacancy__created_by=request.user,
            status="completed",
            analysis_report__isnull=False,
        ).select_related("application__candidate", "application__vacancy")

        # Sort by score
        ranked_sessions = sorted(
            sessions,
            key=lambda s: s.get_score_percentage(),
            reverse=True,
        )

        ranking_data = []
        for rank, session in enumerate(ranked_sessions, 1):
            report = session.analysis_report

            ranking_data.append(
                {
                    "rank": rank,
                    "candidate": {
                        "id": session.application.candidate.id,
                        "name": session.application.candidate.name,
                        "email": session.application.candidate.email,
                    },
                    "vacancy_title": session.application.vacancy.puesto,
                    "score": report.get("quantitative_score"),
                    "score_category": report.get("score_category"),
                    "completed_at": session.completed_at.isoformat()
                    if session.completed_at
                    else None,
                    "session_id": session.id,
                    "summary": {
                        "strengths_count": len(
                            report.get("swot_analysis", {}).get("strengths", [])
                        ),
                        "weaknesses_count": len(
                            report.get("swot_analysis", {}).get("weaknesses", [])
                        ),
                        "top_recommendation": report.get("recommendations", [""])[0]
                        if report.get("recommendations")
                        else "",
                    },
                }
            )

        return Response(
            {
                "total_candidates": len(ranking_data),
                "ranking": ranking_data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="global-report")
    def global_report(self, request):
        """
        Get aggregated company-wide report (company-only)
        """
        if request.user.role != "company":
            return Response(
                {"detail": "Solo empresas"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            analysis_service = InterviewAnalysisService()
            report = analysis_service.generate_global_report(request.user)

            return Response(report, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error generating global report: {e}", exc_info=True)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
