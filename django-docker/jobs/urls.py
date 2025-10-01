from django.urls import path  # type: ignore
from . import views

urlpatterns = [
    path("crear/", views.create_vacante, name="crear_vacante"),
    path("editar/<int:vacante_id>/", views.edit_vacante, name="editar_vacante"),
    path("cerrar/<int:vacante_id>/", views.close_vacante, name="cerrar_vacante"),
    path("guardar/", views.save_vacante, name="guardar_vacante"),
]
