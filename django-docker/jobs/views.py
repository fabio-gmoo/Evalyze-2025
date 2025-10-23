from rest_framework import viewsets, permissions, status as http_status  # type: ignore
from rest_framework.decorators import action  # type: ignore
from rest_framework.response import Response  # type: ignore
from .models import Vacante, Application
from .serializers import VacanteSerializer, ApplicationSerializer
import httpx  # type: ignore
from django.db.models import Q  # type: ignore
import logging
import os

logger = logging.getLogger(__name__)


class VacanteViewSet(viewsets.ModelViewSet):
    queryset = Vacante.objects.all().order_by("-created_at")
    serializer_class = VacanteSerializer
    # ajusta a tu auth si ya la tienes
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        company_name = ""
        if user and hasattr(user, "company_profile"):
            company_name = user.company_profile.company_name

        serializer.save(created_by=user, company_name=company_name)

    @action(detail=False, methods=["get"], url_path="all-vacancies")
    def all_vacancies(self, request):
        """
        Obtiene todas las vacantes del usuario autenticado.
        Parámetros opcionales:
        - active: true/false (filtrar por estado activo)
        - search: texto para buscar en título o descripción
        - ordering: campo para ordenar (ej: -created_at, titulo)
        """
        # Filtrar vacantes del usuario autenticado
        queryset = self.get_queryset()

        # Filtro opcional: solo activas
        active = request.query_params.get("active", None)
        if active is not None:
            is_active = active.lower() == "true"
            queryset = queryset.filter(activo=is_active)

        # Filtro opcional: búsqueda
        search = request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) | Q(descripcion__icontains=search)
            )

        # Ordenamiento opcional (default: más recientes primero)
        ordering = request.query_params.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Sin paginación
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=200)

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        user = getattr(request, "user", None)
        qs = self.get_queryset()
        if getattr(user, "is_authenticated", False):
            qs = qs.filter(created_by=user)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        qs = self.get_queryset()
        data = {
            "active": qs.filter(activa=True).count(),
            "candidates": 247,  # si luego conectas con postulantes reales, reemplaza
            "interviews": 89,
            "hires": 23,
        }
        return Response(data)

    @action(detail=True, methods=["patch"], url_path="close")
    def close(self, request, pk=None):
        vac = self.get_object()
        vac.activa = False
        vac.save(update_fields=["activa"])
        return Response(self.get_serializer(vac).data)

    @action(detail=True, methods=["patch"], url_path="reopen")
    def reopen(self, request, pk=None):
        vac = self.get_object()
        vac.activa = True
        vac.save(update_fields=["activa"])
        return Response(self.get_serializer(vac).data)

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicate(self, request, pk=None):
        src = self.get_object()
        dup = Vacante.objects.create(
            puesto=f"{src.puesto} (copia)",
            descripcion=src.descripcion,
            requisitos=src.requisitos,
            ubicacion=src.ubicacion,
            salario=src.salario,
            tipo_contrato=src.tipo_contrato,
            activa=True,
            departamento=src.departamento,
            created_by=src.created_by,
        )
        return Response(
            self.get_serializer(dup).data, status=http_status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["post"], url_path="generate-ai")
    def generate_ai(self, request):
        title = (request.data or {}).get("puesto", "").strip()
        if not title:
            return Response({"detail": "Falta 'puesto'."}, status=400)

        payload = {
            "puesto": title,
            "descripcion": request.data.get("descripcion")
            or "Descripción base para el puesto",
            "ubicacion": request.data.get("ubicacion") or "A definir",
            "salario": request.data.get("salario"),
            "tipo_contrato": request.data.get("tipo_contrato"),
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "http://interview:9000/ai/vacants/draft",
                    json=payload,
                )
                response.raise_for_status()

                # Si llegamos aquí, fue exitoso
                fastapi_data = response.json()
                frontend_data = {
                    "descripcion": fastapi_data.get("descripcion_sugerida", ""),
                    "requisitos": fastapi_data.get("requisitos_sugeridos", []),
                    "responsabilidades": [],
                    "preguntas": [],
                }
                return Response(frontend_data, status=200)

        except httpx.HTTPStatusError as e:
            # ESTE ES EL PROBLEMA - FastAPI devuelve 400 pero tu frontend no lo maneja
            error_detail = "Error al generar contenido"

            try:
                error_data = e.response.json()
                detail = error_data.get("detail", {})

                if isinstance(detail, dict):
                    # Error de moderación estructurado
                    error_detail = detail.get("message", "Contenido inapropiado")
                elif isinstance(detail, str):
                    error_detail = detail

            except:
                error_detail = e.response.text

            # CRÍTICO: Devolver el error correctamente
            return Response(
                {"error": error_detail},  # ← Cambiar "detail" a "error"
                status=400,
            )

        except Exception as e:
            return Response({"error": f"Error de conexión: {str(e)}"}, status=500)

    @action(detail=False, methods=["post"], url_path="save")
    def create_vacante(self, request):
        data = dict(request.data)
        if "place" in data and "ubicacion" not in data:
            data["ubicacion"] = data.pop("place")

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

        user = (
            request.user if getattr(request.user, "is_authenticated", False) else None
        )
        # Calcula automáticamente el nombre de la empresa si el usuario tiene CompanyProfile
        company_name = ""
        if user and hasattr(user, "company_profile"):
            company_name = user.company_profile.company_name

        obj = serializer.save(created_by=user, company_name=company_name)
        return Response(
            self.get_serializer(obj).data, status=http_status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, pk=None):
        """Candidate applies to a vacancy"""
        vacancy = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Debes iniciar sesión para postular"},
                status=http_status.HTTP_401_UNAUTHORIZED,
            )

        if user.role != "candidate":
            return Response(
                {"detail": "Solo los candidatos pueden postular"},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        # Check if already applied
        if Application.objects.filter(vacancy=vacancy, candidate=user).exists():
            return Response(
                {"detail": "Ya has postulado a esta vacante"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # Create application
        application = Application.objects.create(
            vacancy=vacancy, candidate=user, status="pending"
        )

        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="applications")
    def applications(self, request, pk=None):
        """Get all applications for a vacancy (company only)"""
        vacancy = self.get_object()

        # Only creator can see applications
        if vacancy.created_by != request.user:
            return Response(
                {"detail": "No autorizado"}, status=http_status.HTTP_403_FORBIDDEN
            )

        apps = vacancy.applications.all()
        serializer = ApplicationSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my-applications/")
    def my_applications(self, request):
        """Get candidate's applications"""
        user = request.user

        if user.role != "candidate":
            return Response(
                {"detail": "Solo candidatos"}, status=http_status.HTTP_403_FORBIDDEN
            )

        apps = Application.objects.filter(candidate=user)
        serializer = ApplicationSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="generate-interview")
    def generate_interview(self, request, pk=None):
        """

        Generate interview questions based on vacancy requirements using AI

        AND send the questions to the interview-svc to start candidate chats.

        """

        vacancy = self.get_object()

        # Parse requirements

        requisitos = []

        if isinstance(vacancy.requisitos, str):
            requisitos = [
                r.strip() for r in vacancy.requisitos.split("\n") if r.strip()
            ]

        if not requisitos:
            return Response(
                {"detail": "La vacante no tiene requisitos definidos"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        level = request.data.get("level", "intermedio")

        n_questions = int(request.data.get("n_questions", 4))

        ai_payload = {
            "vacancy_title": vacancy.puesto,
            "requirements": requisitos,
            "level": level,
            "n_questions": n_questions,
        }

        try:
            # FIX: Open the client context manager for the entire operation

            with httpx.Client(timeout=300.0) as client:
                # --- 1. CALL AI-SERVICE TO GET QUESTIONS (Host: ai-service, Port: 8001) ---

                ai_response = client.post(
                    "http://ai-service:8001/generate_interview",
                    json=ai_payload,
                )

                ai_response.raise_for_status()

                ai_data = ai_response.json()

                if not ai_data.get("ok"):
                    return Response(
                        {"detail": "Error generando entrevista en el AI Service"},
                        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                generated_interview = ai_data["interview"]

                # --- 2. GET CANDIDATE LIST ---

                applied_candidates = []

                for app in vacancy.applications.all().select_related("candidate"):
                    applied_candidates.append(
                        {
                            "id": app.candidate.id,
                            "email": app.candidate.email,
                            "name": app.candidate.name,
                        }
                    )

                if not applied_candidates:
                    logger.warning(
                        f"No candidates applied to vacancy {
                            vacancy.id
                        }. Skipping conversation start."
                    )

                    return Response(
                        {
                            "interview": generated_interview,
                            "vacancy": {
                                "id": vacancy.id,
                                "puesto": vacancy.puesto,
                                "company": vacancy.company_name,
                            },
                            "chat_status": "No candidates to start conversations with.",
                        },
                        status=http_status.HTTP_200_OK,
                    )

                # --- 3. CALL INTERVIEW-SVC TO START CONVERSATIONS ---

                interview_svc_payload = {
                    "vacancy_id": vacancy.id,
                    "vacancy_title": vacancy.puesto,
                    "interview_questions": generated_interview["questions"],
                    "candidates": applied_candidates,
                }

                interview_svc_api_key = os.environ.get(
                    "AI_PUBLIC_API_KEY", "your-fallback-key"
                )

                interview_svc_headers = {"X-Api-Key": interview_svc_api_key}

                # CRITICAL FIX: Final correct path using Docker service name and matching path

                INTERVIEW_SVC_URL = (
                    "http://interview:9000/ai/candidate-conversations/start"
                )

                interview_svc_response = client.post(
                    INTERVIEW_SVC_URL,  # <--- Now targeting 'interview' on port 9000
                    json=interview_svc_payload,
                    headers=interview_svc_headers,
                )

                interview_svc_response.raise_for_status()

                chat_data = interview_svc_response.json()

                # --- 4. RETURN FINAL RESPONSE ---

                return Response(
                    {
                        "interview": generated_interview,
                        "vacancy": {
                            "id": vacancy.id,
                            "puesto": vacancy.puesto,
                            "company": vacancy.company_name,
                        },
                        "chat_status": chat_data.get(
                            "status", "Conversations initiated."
                        ),
                        "started_chats": chat_data.get("started_chats", []),
                    },
                    status=http_status.HTTP_200_OK,
                )

        except httpx.HTTPStatusError as e:
            # Handle error from AI-Service or Interview-Service

            return Response(
                {"detail": f"Error en servicio de IA/Chat: {e.response.text}"},
                status=http_status.HTTP_502_BAD_GATEWAY,
            )

        except Exception as e:
            logger.error(f"Error en el flujo de entrevista/chat: {e}", exc_info=True)

            return Response(
                {"detail": f"Error interno: {str(e)}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_ai_interview_data(
        self, vacancy, level: str = "intermedio", n_questions: int = 4
    ):
        """Internal helper to call the AI service and get interview questions."""

        # NOTE: Ensure vacancy.requisitos is a string for the splitlines() method
        # if it's not automatically converted from the ListField representation on access.
        # Your serializer handles the conversion, but here we enforce list parsing.
        requisitos = []
        if isinstance(vacancy.requisitos, str):
            requisitos = [
                r.strip() for r in vacancy.requisitos.splitlines() if r.strip()
            ]
        elif isinstance(vacancy.requisitos, list):
            requisitos = [r.strip() for r in vacancy.requisitos if r.strip()]

        if not requisitos:
            raise ValueError("La vacante no tiene requisitos definidos.")

        ai_payload = {
            "vacancy_title": vacancy.puesto,
            "requirements": requisitos,
            "level": level,
            "n_questions": n_questions,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                ai_response = client.post(
                    "http://ai-service:8001/generate_interview",
                    json=ai_payload,
                )
                ai_response.raise_for_status()
                ai_data = ai_response.json()

            if not ai_data.get("ok"):
                # Handle cases where the AI service responds 200 but signals an internal error
                raise Exception(
                    f"AI Service internal error: {
                        ai_data.get('detail', 'Unknown error')
                    }"
                )

            return ai_data["interview"]

        except httpx.HTTPStatusError as e:
            logger.error(f"Error calling AI service: {e.response.text}")
            raise ConnectionError(
                f"Error al generar entrevista en AI Service: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Internal error during AI call: {e}")
            # Note: If this fails, the question generation failed, so the chat can't start.
            raise ConnectionError(f"Error interno al conectar con AI Service: {e}")

    @action(detail=True, methods=["post"], url_path="start-candidate-chat")
    def start_candidate_chat(self, request, pk=None):
        """
        Candidate calls this endpoint to start an individual AI interview session.
        1. Gets interview questions from AI-Service.
        2. Tells Interview-Service to start the individual session for this candidate.
        """
        vacancy = self.get_object()
        user = request.user

        if not user.is_authenticated or user.role != "candidate":
            return Response(
                {"detail": "Acceso denegado."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        # Use default values provided by the Angular frontend
        level = request.data.get("level", "intermedio")
        n_questions = int(request.data.get("n_questions", 4))

        try:
            # 1. CALL AI-SERVICE TO GET QUESTIONS
            generated_interview = self._get_ai_interview_data(
                vacancy, level=level, n_questions=n_questions
            )
            questions = generated_interview["questions"]

            # 2. CALL INTERVIEW-SVC TO START INDIVIDUAL CONVERSATION (Using PLURAL KEY)

            INTERVIEW_SVC_URL = "http://interview:9000/ai/candidate-conversations/start"

            interview_svc_payload = {
                "vacancy_id": vacancy.id,
                "vacancy_title": vacancy.puesto,
                # The Interview Service is likely expecting the structured question objects
                "interview_questions": questions,
                # CRITICAL FIX: Wrap the single candidate in a list and use the PLURAL key 'candidates'
                "candidates": [
                    {
                        "id": user.id,
                        "email": user.email,
                        # Fallback to email if first_name/last_name are empty
                        "name": f"{user.first_name} {user.last_name}".strip()
                        or user.email,
                    }
                ],
            }

            interview_svc_api_key = os.environ.get(
                "AI_PUBLIC_API_KEY", "your-fallback-key"
            )
            interview_svc_headers = {"X-Api-Key": interview_svc_api_key}

            with httpx.Client(timeout=60.0) as client:
                interview_svc_response = client.post(
                    INTERVIEW_SVC_URL,
                    json=interview_svc_payload,
                    headers=interview_svc_headers,
                )
                interview_svc_response.raise_for_status()
                chat_data = interview_svc_response.json()

            # CRITICAL: Return session ID and first message/questions for the frontend
            return Response(
                {
                    "session_id": chat_data.get("session_id"),
                    "initial_message": chat_data.get(
                        "initial_message",
                        "Hola, estoy listo para iniciar tu entrevista.",
                    ),
                    "questions": questions,
                },
                status=http_status.HTTP_200_OK,
            )

        except (ValueError, ConnectionError) as e:
            # Error handling for known issues (missing requirements, connection failure)
            logger.error(f"Error en el flujo de chat (Requisitos/Conexión): {e}")
            return Response(
                {"detail": f"Error: {e}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            # Catch-all for unexpected issues
            logger.error(f"Error inesperado al iniciar chat: {e}", exc_info=True)
            return Response(
                {"detail": f"Error interno inesperado: {str(e)}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
