# serializers.py
from rest_framework import serializers  # type: ignore
from .models import Vacante


class VacanteSerializer(serializers.ModelSerializer):
    requisitos = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    salario = serializers.SerializerMethodField()

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
            "salariomin",
            "salariomax",
        ]
        read_only_fields = ("salario",)

    def get_salario(self, obj):
        if obj.salariomin and obj.salariomax:
            return f"{obj.salariomin} - {obj.salariomax}"
        if obj.salariomin:
            return str(obj.salariomin)
        if obj.salariomax:
            return str(obj.salariomax)
        return "A convenir"

    def to_internal_value(self, data):
        data = dict(data)

        # Si requisitos viene como string (aunque idealmente no), permitirlo
        if "requisitos" in data and isinstance(data["requisitos"], str):
            data["requisitos"] = [
                r.strip() for r in data["requisitos"].splitlines() if r.strip()
            ]

        # Procesamiento de salario (igual que antes)
        sal = data.get("salario")
        if isinstance(sal, str) and "-" in sal:
            parts = [p.strip() for p in sal.split("-", 1)]
            data["salariomin"] = parts[0]
            data["salariomax"] = parts[1]
        else:
            if "salarioMin" in data:
                data["salariomin"] = data.pop("salarioMin")
            if "salarioMax" in data:
                data["salariomax"] = data.pop("salarioMax")

        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        raw = getattr(instance, "requisitos", None)
        # Si en el modelo requisitos es texto (string), convertir a lista
        if isinstance(raw, str):
            lines = [r.strip() for r in raw.splitlines() if r.strip()]
            rep["requisitos"] = lines
        # Si ya es lista (por ejemplo usando ArrayField), no tocar
        return rep

    def create(self, validated_data):
        req_list = validated_data.pop("requisitos", [])
        # Si se envió lista, convertirla a string multilinea para almacenar
        if isinstance(req_list, list):
            validated_data["requisitos"] = "\n".join(req_list)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        req_list = validated_data.pop("requisitos", None)
        if req_list is not None and isinstance(req_list, list):
            instance.requisitos = "\n".join(req_list)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
