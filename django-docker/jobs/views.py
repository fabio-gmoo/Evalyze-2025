from rest_framework import viewsets, permissions, status as http_status  # type: ignore
from rest_framework.decorators import action  # type: ignore
from rest_framework.response import Response  # type: ignore
from .models import Vacante
from .serializers import VacanteSerializer
import httpx  # type: ignore
from django.db.models import Q  # type: ignore
import logging

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
