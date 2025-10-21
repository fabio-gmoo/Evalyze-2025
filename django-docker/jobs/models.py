from django.db import models  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore
from django.utils import timezone  # type: ignore

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
    company_name = models.CharField(max_length=200, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vacantes_created",
    )

    def __str__(self):
        return f"{self.puesto} - {self.company_name or self.ubicacion}"

    @property
    def applications_count(self):
        """Number of candidates who applied"""
        return self.applications.count()


class Application(models.Model):
    """Relation between Candidate and Vacancy"""

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("reviewing", "En Revisión"),
        ("interview", "Entrevista"),
        ("accepted", "Aceptado"),
        ("rejected", "Rechazado"),
    ]

    vacancy = models.ForeignKey(
        Vacante, on_delete=models.CASCADE, related_name="applications"
    )
    candidate = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("vacancy", "candidate")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate.email} → {self.vacancy.puesto}"
