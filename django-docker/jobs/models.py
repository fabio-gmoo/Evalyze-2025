from django.db import models  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore

User = get_user_model()


class Vacante(models.Model):
    puesto = models.CharField(max_length=150)
    descripcion = models.TextField()
    requisitos = models.TextField(blank=True, default="")
    ubicacion = models.CharField(max_length=120)
    salariomin = models.CharField(max_length=100, blank=True, null=True)
    salariomax = models.CharField(max_length=100, blank=True, null=True)
    tipo_contrato = models.CharField(max_length=60, blank=True, null=True)
    activa = models.BooleanField(default=True)
    departamento = models.CharField(max_length=120, blank=True, default="")

    # NEW FIELD
    company_name = models.CharField(max_length=200, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="vacantes"
    )

    def __str__(self) -> str:
        return f"{self.puesto} - {self.company_name or self.ubicacion}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
