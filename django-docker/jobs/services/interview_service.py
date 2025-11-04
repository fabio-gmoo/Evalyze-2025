# django-docker/jobs/services/interview_service.py

import httpx  # type: ignore
import logging
from typing import Dict, List
from jobs.models import InterviewSession, ChatMessage, Application

logger = logging.getLogger(__name__)

AI_SERVICE_URL = "http://ai-service:8001"


class InterviewService:
    """Service to manage AI interview sessions"""

    def __init__(self):
        self.ai_url = AI_SERVICE_URL

    def create_session_for_application(
        self, application: Application, interview_questions: List[Dict]
    ) -> InterviewSession:
        """
        Create an interview session when a candidate applies
        """
        # Create the session record
        session = InterviewSession.objects.create(
            application=application,
            interview_config={
                "questions": interview_questions,
                "vacancy_id": application.vacancy.id,
                "vacancy_title": application.vacancy.puesto,
            },
            max_possible_score=sum(q.get("weight", 0) for q in interview_questions),
        )

        logger.info(
            f"Created interview session {session.id} for application {application.id}"
        )
        return session

    def start_interview(self, session: InterviewSession) -> Dict:
        """
        Start the AI interview session
        """
        if session.status != "pending":
            raise ValueError(f"Session {session.id} is not in pending state")

        # Build system prompt for AI
        system_prompt = self._build_system_prompt(session)

        try:
            # Call AI service to start chat
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.ai_url}/chat/start",
                    json={"system": system_prompt, "model": "llama3.2"},
                )
                response.raise_for_status()
                data = response.json()

            # Extract AI session ID and first message
            ai_session_id = data.get("session_id")
            first_message = data.get("message")

            # Update session
            session.start_session(ai_session_id)

            # Save first message
            ChatMessage.objects.create(
                session=session, sender="ai", content=first_message, question_index=0
            )

            logger.info(
                f"Started AI session {ai_session_id} for interview {session.id}"
            )

            return {
                "session_id": session.id,
                "ai_session_id": ai_session_id,
                "first_message": first_message,
                "status": "active",
            }

        except Exception as e:
            logger.error(f"Error starting interview: {e}", exc_info=True)
            raise

    def send_message(self, session: InterviewSession, candidate_message: str) -> Dict:
        """
        Send candidate message to AI and get response
        """
        if not session.is_active():
            raise ValueError(f"Session {session.id} is not active")

        # Save candidate message
        candidate_msg = ChatMessage.objects.create(
            session=session,
            sender="candidate",
            content=candidate_message,
            question_index=session.current_question_index,
        )

        try:
            # Send to AI service
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.ai_url}/chat/message",
                    json={
                        "session_id": session.ai_session_id,
                        "text": candidate_message,
                        "model": "llama3.2",
                    },
                )
                response.raise_for_status()
                data = response.json()

            ai_response = data.get("message")

            # Save AI response
            ai_msg = ChatMessage.objects.create(
                session=session,
                sender="ai",
                content=ai_response,
                question_index=session.current_question_index,
            )

            # Check if we should move to next question
            total_questions = len(session.interview_config.get("questions", []))
            if session.current_question_index < total_questions - 1:
                session.current_question_index += 1
                session.save()
            else:
                # Interview complete
                self._complete_interview(session)

            return {
                "message": ai_response,
                "current_question": session.current_question_index,
                "total_questions": total_questions,
                "is_complete": session.status == "completed",
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            raise

    def get_session_history(self, session: InterviewSession) -> List[Dict]:
        """
        Get all messages in a session
        """
        messages = session.messages.all()
        return [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "score": msg.score,
            }
            for msg in messages
        ]

    def _build_system_prompt(self, session: InterviewSession) -> str:
        """
        Build the system prompt for the AI interviewer
        """
        config = session.interview_config
        questions = config.get("questions", [])
        vacancy_title = config.get("vacancy_title", "esta posición")

        questions_text = "\n".join(
            [
                f"{i + 1}. {q.get('question')} (Tipo: {q.get('type')}, Peso: {
                    q.get('weight')
                }%)"
                for i, q in enumerate(questions)
            ]
        )

        prompt = f"""Eres un entrevistador profesional de IA para Evalyze.

VACANTE: {vacancy_title}

TU MISIÓN:
1. Conducir una entrevista profesional y amigable
2. Hacer las siguientes preguntas una por una
3. Escuchar atentamente las respuestas del candidato
4. Hacer preguntas de seguimiento cuando sea apropiado
5. Evaluar las respuestas basándote en las palabras clave esperadas

PREGUNTAS DE LA ENTREVISTA:
{questions_text}

INSTRUCCIONES:
- Empieza con un saludo cálido y preséntate
- Haz UNA pregunta a la vez
- Espera la respuesta antes de continuar
- Sé empático y profesional
- Al final, agradece al candidato por su tiempo

Responde SIEMPRE en español y mantén un tono profesional pero amigable."""

        return prompt

    def _complete_interview(self, session: InterviewSession):
        """
        Mark interview as complete and calculate final score
        """
        # TODO: Implement scoring logic based on AI evaluations
        session.complete_session()
        logger.info(f"Completed interview session {session.id}")
