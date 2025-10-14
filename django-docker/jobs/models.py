from django.db import models  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore

User = get_user_model()


class Vacante(models.Model):
    puesto = models.CharField(max_length=150)
    descripcion = models.TextField()
    # Guardamos requisitos como texto (líneas), pero el API los expone como string[]
    requisitos = models.TextField(blank=True, default="")
    ubicacion = models.CharField(max_length=120)
    # "45000 - 65000", "A convenir", etc.
    salariomin = models.CharField(max_length=100, blank=True, null=True)
    # "45000 - 65000", "A convenir", etc.
    salariomax = models.CharField(max_length=100, blank=True, null=True)
    # "Tiempo Completo", etc.
    tipo_contrato = models.CharField(max_length=60, blank=True, null=True)
    activa = models.BooleanField(default=True)

    # Campos útiles para /mine/ y duplicado
    departamento = models.CharField(max_length=120, blank=True, default="")
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="vacantes"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.puesto} - {self.ubicacion}"
