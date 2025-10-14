from rest_framework import viewsets, permissions, status as http_status  # type: ignore
from rest_framework.decorators import action  # type: ignore
from rest_framework.response import Response  # type: ignore
from .models import Vacante
from .serializers import VacanteSerializer
import httpx  # type: ignore
from asgiref.sync import async_to_sync  # type: ignore
import traceback


class VacanteViewSet(viewsets.ModelViewSet):
    queryset = Vacante.objects.all().order_by("-created_at")
    serializer_class = VacanteSerializer
    # ajusta a tu auth si ya la tienes
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = getattr(self.request, "user", None)
        serializer.save(
            created_by=user if getattr(user, "is_authenticated", False) else None
        )

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

                # Transformar la respuesta de FastAPI al formato que espera el frontend
                fastapi_data = response.json()
                frontend_data = {
                    "descripcion": fastapi_data.get("descripcion_sugerida", ""),
                    "requisitos": fastapi_data.get("requisitos_sugeridos", []),
                    "responsabilidades": [],  # FastAPI no devuelve esto
                    "preguntas": [],  # FastAPI no devuelve esto
                }

                return Response(frontend_data, status=200)

        except httpx.HTTPStatusError as e:
            return Response(
                {"detail": f"Error de FastAPI: {e.response.text}"}, status=502
            )

    @action(detail=False, methods=["post"], url_path="save")
    def create_vacante(self, request):
        # Permitimos que el serializer maneje validación y conversiones
        data = dict(request.data)
        # Alias: permitir que el frontend envíe 'place' en vez de 'ubicacion'
        if "place" in data and "ubicacion" not in data:
            data["ubicacion"] = data.pop("place")

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

        user = (
            request.user
            if hasattr(request, "user")
            and getattr(request.user, "is_authenticated", False)
            else None
        )
        try:
            obj = serializer.save(created_by=user)
            return Response(
                self.get_serializer(obj).data, status=http_status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": f"Error al crear vacante: {str(e)}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
