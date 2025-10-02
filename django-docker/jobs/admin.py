from django.contrib import admin  # type: ignore
from .models import Vacante

@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ("id", "puesto", "ubicacion", "tipo_contrato", "activa", "created_at")
    search_fields = ("puesto", "ubicacion", "descripcion", "requisitos")
    list_filter = ("activa", "tipo_contrato", "created_at")

