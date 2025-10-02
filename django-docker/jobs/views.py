from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Vacante
from .serializers import VacanteSerializer

class VacanteViewSet(viewsets.ModelViewSet):
    queryset = Vacante.objects.all().order_by("-created_at")
    serializer_class = VacanteSerializer
    permission_classes = [permissions.AllowAny]  # ajusta a tu auth si ya la tienes

    def perform_create(self, serializer):
        user = getattr(self.request, "user", None)
        serializer.save(created_by=user if getattr(user, "is_authenticated", False) else None)

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
            "candidates": 247,     # si luego conectas con postulantes reales, reemplaza
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
        return Response(self.get_serializer(dup).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="generate-ai")
    def generate_ai(self, request):
        title = (request.data or {}).get("puesto", "").strip()
        if not title:
            return Response({"detail": "Falta 'puesto'."}, status=400)

        # Stub simple para que el front funcione ahora mismo
        payload = {
            "descripcion": f"{title}: rol clave en el equipo. Trabajarás con buenas prácticas y colaboración.",
            "requisitos": [
                "3+ años de experiencia relevante",
                "Conocimiento de patrones de diseño",
                "Buenas prácticas de testing",
            ],
            "responsabilidades": [
                "Diseñar, implementar y mantener funcionalidades",
                "Colaborar con equipos multidisciplinarios",
            ],
            "preguntas": [
                {"pregunta": "Cuéntame tu experiencia más reciente en el rol.", "tipo": "Conductual", "peso": 20, "palabras_clave": ["experiencia", "impacto"]},
                {"pregunta": "¿Qué estrategia sigues para testear?", "tipo": "Técnica", "peso": 20, "palabras_clave": ["testing", "calidad"]},
            ],
        }
        return Response(payload, status=200)
