# serializers.py
from rest_framework import serializers  # type: ignore
from .models import Vacante


class VacanteSerializer(serializers.ModelSerializer):
    # Exponemos requisitos como lista en la API
    requisitos = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    # Campo calculado para mantener compatibilidad con frontend: "45000 - 65000" | "A convenir"
    salario = serializers.SerializerMethodField()

    class Meta:
        model = Vacante
        # Incluimos salariomin/salariomax como campos del modelo (si quieres que sean visibles, opcional).
        fields = [
            "id",
            "puesto",
            "descripcion",
            "requisitos",
            "ubicacion",
            "salario",  # string compuesto que usa el frontend
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

    # Acepta 'requisitos' como string multilínea o lista; y convierte 'salario' compuesto a campos separados.
    def to_internal_value(self, data):
        data = dict(data)  # copia para no mutar original

        # requisitos: permitir string multilínea
        if "requisitos" in data and isinstance(data["requisitos"], str):
            data["requisitos"] = [
                r.strip() for r in data["requisitos"].splitlines() if r.strip()
            ]

        # aceptar 'salario' compuesto: "123 - 456" -> salariomin / salariomax
        sal = data.get("salario")
        if isinstance(sal, str) and "-" in sal:
            parts = [p.strip() for p in sal.split("-", 1)]
            data["salariomin"] = parts[0]
            data["salariomax"] = parts[1]
        else:
            # también aceptar salarioMin / salarioMax (nombres que viene del front)
            if "salarioMin" in data:
                data["salariomin"] = data.pop("salarioMin")
            if "salarioMax" in data:
                data["salariomax"] = data.pop("salarioMax")

        return super().to_internal_value(data)

    def create(self, validated_data):
        # validated_data["requisitos"] -> list; guardar como texto
        req_list = validated_data.pop("requisitos", [])
        if isinstance(req_list, list):
            validated_data["requisitos"] = "\n".join(req_list)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        req_list = validated_data.pop("requisitos", None)
        if req_list is not None:
            instance.requisitos = "\n".join(req_list)
        # El resto lo maneja el update normal
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
