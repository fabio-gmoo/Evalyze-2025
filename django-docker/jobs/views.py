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
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        company_name = ""
        if user and hasattr(user, "company_profile"):
            company_name = user.company_profile.company_name

        serializer.save(created_by=user, company_name=company_name)

    @action(detail=False, methods=["get"], url_path="all-vacancies")
    def all_vacancies(self, request):
        queryset = self.get_queryset()
        active = request.query_params.get("active", None)
        if active is not None:
            is_active = active.lower() == "true"
            queryset = queryset.filter(activo=is_active)

        search = request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) | Q(descripcion__icontains=search)
            )

        ordering = request.query_params.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

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
            "candidates": Application.objects.count(),  # Fix: usar conteo real
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
                fastapi_data = response.json()
                frontend_data = {
                    "descripcion": fastapi_data.get("descripcion_sugerida", ""),
                    "requisitos": fastapi_data.get("requisitos_sugeridos", []),
                    "responsabilidades": [],
                    "preguntas": [],
                }
                return Response(frontend_data, status=200)

        except httpx.HTTPStatusError as e:
            error_detail = "Error al generar contenido"
            try:
                error_data = e.response.json()
                detail = error_data.get("detail", {})
                if isinstance(detail, dict):
                    error_detail = detail.get("message", "Contenido inapropiado")
                elif isinstance(detail, str):
                    error_detail = detail
            except:
                error_detail = e.response.text
            return Response({"error": error_detail}, status=400)

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
        company_name = ""
        if user and hasattr(user, "company_profile"):
            company_name = user.company_profile.company_name

        obj = serializer.save(created_by=user, company_name=company_name)
        return Response(
            self.get_serializer(obj).data, status=http_status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, pk=None):
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

        if Application.objects.filter(vacancy=vacancy, candidate=user).exists():
            return Response(
                {"detail": "Ya has postulado a esta vacante"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        interview_questions = self._get_interview_questions(vacancy)
        if not interview_questions:
            return Response(
                {
                    "detail": "Esta vacante no tiene preguntas de entrevista configuradas"
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        application = Application.objects.create(
            vacancy=vacancy, candidate=user, status="pending"
        )

        from .services.interview_service import InterviewService

        service = InterviewService()

        try:
            session = service.create_session_for_application(
                application=application, interview_questions=interview_questions
            )
            return Response(
                {
                    "application": ApplicationSerializer(application).data,
                    "interview_session": {
                        "id": session.id,
                        "status": session.status,
                        "message": "Sesión de entrevista creada. Puedes iniciarla cuando estés listo.",
                    },
                },
                status=http_status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating interview session: {e}", exc_info=True)
            return Response(
                {
                    "application": ApplicationSerializer(application).data,
                    "interview_session": {
                        "error": "No se pudo crear la sesión de entrevista",
                        "detail": str(e),
                    },
                },
                status=http_status.HTTP_201_CREATED,
            )

    def _get_interview_questions(self, vacancy):
        cache_key = f"interview_questions_vacancy_{vacancy.id}"
        cached_questions = None
        try:
            from django.core.cache import cache  # type: ignore

            cached_questions = cache.get(cache_key)
        except Exception:
            pass

        if cached_questions:
            return cached_questions

        if hasattr(vacancy, "generated_interview") and vacancy.generated_interview:
            questions = vacancy.generated_interview.get("questions", [])
            if questions:
                try:
                    from django.core.cache import cache  # type: ignore

                    cache.set(cache_key, questions, 3600)
                except Exception:
                    pass
                return questions

        logger.warning(f"No interview questions found for vacancy {vacancy.id}")
        return None

    @action(detail=True, methods=["get"], url_path="applications")
    def applications(self, request, pk=None):
        """Obtiene todas las postulaciones para una vacante (solo empresa)"""
        vacancy = self.get_object()

        # Validación de seguridad: Solo el creador ve los candidatos
        if vacancy.created_by != request.user:
            return Response(
                {"detail": "No autorizado"}, status=http_status.HTTP_403_FORBIDDEN
            )

        # Optimización: Traemos candidato y la sesión de entrevista (reverse relationship)
        # 'interview_session' es el related_name en Application -> InterviewSession
        apps = (
            vacancy.applications.all()
            .select_related("candidate")
            .prefetch_related("interview_session")
        )

        serializer = ApplicationSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my-applications/")
    def my_applications(self, request):
        user = request.user
        if user.role != "candidate":
            return Response(
                {"detail": "Solo candidatos"}, status=http_status.HTTP_403_FORBIDDEN
            )
        apps = Application.objects.filter(candidate=user).select_related(
            "vacancy", "interview_session"
        )
        serializer = ApplicationSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="generate-interview")
    def generate_interview(self, request, pk=None):
        vacancy = self.get_object()
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
            with httpx.Client(timeout=300.0) as client:
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
                vacancy.generated_interview = generated_interview
                vacancy.save(update_fields=["generated_interview"])

                cache_key = f"interview_questions_vacancy_{vacancy.id}"
                from django.core.cache import cache  # type: ignore

                cache.set(cache_key, generated_interview["questions"], 3600)

                applied_candidates = []
                for app in vacancy.applications.all().select_related("candidate"):
                    applied_candidates.append(
                        {
                            "id": app.candidate.id,
                            "email": app.candidate.email,
                            "name": app.candidate.name,
                        }
                    )

                return Response(
                    {
                        "interview": generated_interview,
                        "vacancy": {
                            "id": vacancy.id,
                            "puesto": vacancy.puesto,
                            "company": vacancy.company_name,
                        },
                        "saved": True,
                        "questions_count": len(
                            generated_interview.get("questions", [])
                        ),
                        "candidates_count": len(applied_candidates),
                        "message": "Preguntas guardadas exitosamente.",
                    },
                    status=http_status.HTTP_200_OK,
                )

        except httpx.HTTPStatusError as e:
            return Response(
                {"detail": f"Error en servicio de IA: {e.response.text}"},
                status=http_status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.error(f"Error en generate_interview: {e}", exc_info=True)
            return Response(
                {"detail": f"Error interno: {str(e)}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_ai_interview_data(
        self, vacancy, level: str = "intermedio", n_questions: int = 4
    ):
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
            raise ConnectionError(f"Error interno al conectar con AI Service: {e}")

    @action(detail=True, methods=["post"], url_path="start-candidate-chat")
    def start_candidate_chat(self, request, pk=None):
        vacancy = self.get_object()
        user = request.user

        if not user.is_authenticated or user.role != "candidate":
            return Response(
                {"detail": "Acceso denegado."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        level = request.data.get("level", "intermedio")
        n_questions = int(request.data.get("n_questions", 4))

        try:
            generated_interview = self._get_ai_interview_data(
                vacancy, level=level, n_questions=n_questions
            )
            questions = generated_interview["questions"]

            INTERVIEW_SVC_URL = "http://interview:9000/ai/candidate-conversations/start"
            interview_svc_payload = {
                "vacancy_id": vacancy.id,
                "vacancy_title": vacancy.puesto,
                "interview_questions": questions,
                "candidates": [
                    {
                        "id": user.id,
                        "email": user.email,
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
            logger.error(f"Error en el flujo de chat (Requisitos/Conexión): {e}")
            return Response(
                {"detail": f"Error: {e}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(f"Error inesperado al iniciar chat: {e}", exc_info=True)
            return Response(
                {"detail": f"Error interno inesperado: {str(e)}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
