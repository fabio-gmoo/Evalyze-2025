# django-docker/jobs/views_interview.py

from rest_framework import viewsets, status  # type: ignore
from rest_framework.decorators import action  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.permissions import IsAuthenticated  # type: ignore
from .models import InterviewSession, ChatMessage
from .services.interview_service import InterviewService  # type: ignore
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
        if request.user.role != "candidate":
            return Response(
                {"detail": "Solo candidatos pueden acceder"},
                status=status.HTTP_403_FORBIDDEN,
            )

        active_session = (
            InterviewSession.objects.filter(
                application__candidate=request.user,
                status__in=["pending", "active"],  # ← FIXED: Include pending
            )
            .order_by("-started_at", "-id")  # Get the most recent
            .first()
        )

        if not active_session:
            return Response({"session": None})

        serializer = self.get_serializer(active_session)
        return Response({"session": serializer.data})
