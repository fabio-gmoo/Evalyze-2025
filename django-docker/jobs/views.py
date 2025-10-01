from django.http import JsonResponse  # type: ignore
import json
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from django.core.exceptions import ObjectDoesNotExist  # type: ignore
from .models import Vacante


@csrf_exempt
def create_vacante(request):
    if request.method == "POST":
        data = json.loads(request.body)
        vacante = Vacante.objects.create(
            puesto=data["puesto"],
            descripcion=data["descripcion"],
            requisitos=data["requisitos"],
            ubicacion=data["ubicacion"],
            salario=data.get("salario", ""),
            tipo_contrato=data.get("tipo_contrato", ""),
        )
        return JsonResponse({"id": vacante.id, "status": "Vacante creada"}, status=201)


@csrf_exempt
def edit_vacante(request, vacante_id):
    if request.method == "PUT":
        try:
            vacante = Vacante.objects.get(id=vacante_id)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Vacante no encontrada"}, status=404)
        data = json.loads(request.body)
        vacante.puesto = data["puesto"]
        vacante.descripcion = data["descripcion"]
        vacante.requisitos = data["requisitos"]
        vacante.ubicacion = data["ubicacion"]
        vacante.salario = data.get("salario", vacante.salario)
        vacante.tipo_contrato = data.get("tipo_contrato", vacante.tipo_contrato)
        vacante.save()
        return JsonResponse({"status": "Vacante actualizada"}, status=200)


@csrf_exempt
def close_vacante(request, vacante_id):
    if request.method == "PATCH":
        try:
            vacante = Vacante.objects.get(id=vacante_id)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Vacante no encontrada"}, status=404)

        vacante.activa = False
        vacante.save()
        return JsonResponse({"status": "Vacante cerrada"}, status=200)


@csrf_exempt
def save_vacante(request):
    if request.method == "POST":
        # Obtener los datos del cuerpo de la solicitud
        data = json.loads(request.body)

        # Si la vacante ya existe, la actualizamos
        vacante, created = Vacante.objects.update_or_create(
            # Aquí podemos usar el id proporcionado para la actualización
            id=data["id"],
            defaults={
                "puesto": data["puesto"],
                "descripcion": data["descripcion"],
                "requisitos": data["requisitos"],
                "ubicacion": data["ubicacion"],
                "salario": data.get("salario", ""),
                "tipo_contrato": data.get("tipo_contrato", ""),
                "activa": True,  # La vacante siempre se activa al ser guardada
            },
        )

        # Respuesta de éxito
        if created:
            return JsonResponse(
                {"status": "Vacante creada con éxito", "id": vacante.id}, status=201
            )
        else:
            return JsonResponse(
                {"status": "Vacante actualizada con éxito", "id": vacante.id},
                status=200,
            )
    else:
        return JsonResponse({"error": "Metodo no permitido"}, status=405)
