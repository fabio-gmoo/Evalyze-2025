from rest_framework import serializers  # type: ignore
from .models import Vacante


class VacanteSerializer(serializers.ModelSerializer):
    requisitos = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    class Meta:
        model = Vacante
        fields = [
            "id",
            "puesto",
            "descripcion",
            "requisitos",
            "ubicacion",
            "salario",
            "tipo_contrato",
            "activa",
            "departamento",
        ]

    # -> Python model
    def to_internal_value(self, data):
        # Acepta 'requisitos' como string (multilínea) o list[str]
        req = data.get("requisitos", [])
        if isinstance(req, str):
            data = dict(data)
            data["requisitos"] = [r.strip() for r in req.splitlines() if r.strip()]
        return super().to_internal_value(data)

    # -> JSON
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["requisitos"] = [
            r for r in (instance.requisitos or "").splitlines() if r.strip()
        ]
        return rep

    def create(self, validated_data):
        # Convertimos list -> text
        req_list = validated_data.pop("requisitos", [])
        obj = Vacante.objects.create(**validated_data, requisitos="\n".join(req_list))
        return obj

    def update(self, instance, validated_data):
        req_list = validated_data.pop("requisitos", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if req_list is not None:
            instance.requisitos = "\n".join(req_list)
        instance.save()
        return instance
