# jobs/models.py
from django.db import models  # type: ignore


class Vacante(models.Model):
    puesto = models.CharField(max_length=100)
    descripcion = models.TextField()
    # Requisitos en formato de texto o como una lista separada por comas
    requisitos = models.TextField()
    ubicacion = models.CharField(max_length=100)
    salario = models.CharField(max_length=100, blank=True, null=True)
    tipo_contrato = models.CharField(max_length=50, blank=True, null=True)
    # True = activa, False = cerrada
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.puesto} - {self.ubicacion}"
