# serializers.py
from rest_framework import serializers  # type: ignore
from .models import Vacante, Application
from django.contrib.auth import get_user_model  # type: ignore

User = get_user_model()


class CreatorSerializer(serializers.ModelSerializer):
    """Serializer for vacancy creator info"""

    name = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "name", "role"]


class VacanteSerializer(serializers.ModelSerializer):
    requisitos = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    salario = serializers.SerializerMethodField()
    company_name = serializers.CharField(read_only=True)

    # NEW: Creator information
    created_by_info = serializers.SerializerMethodField()
    applications_count = serializers.IntegerField(
        source="applications.count", read_only=True
    )

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
            "company_name",
            "created_at",
            "created_by_info",  # NEW
            "applications_count",  # NEW
        ]
        read_only_fields = (
            "salario",
            "created_at",
            "created_by_info",
            "applications_count",
        )

    def get_salario(self, obj):
        if obj.salariomin and obj.salariomax:
            return f"{obj.salariomin} - {obj.salariomax}"
        if obj.salariomin:
            return str(obj.salariomin)
        if obj.salariomax:
            return str(obj.salariomax)
        return "A convenir"

    def get_created_by_info(self, obj):
        """Return creator information"""
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "email": obj.created_by.email,
                "name": obj.created_by.name,  # Uses the @property from User model
                "role": obj.created_by.role,
            }
        return None

    def to_internal_value(self, data):
        data = dict(data)

        if "requisitos" in data and isinstance(data["requisitos"], str):
            data["requisitos"] = [
                r.strip() for r in data["requisitos"].splitlines() if r.strip()
            ]

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
        if isinstance(raw, str):
            lines = [r.strip() for r in raw.splitlines() if r.strip()]
            rep["requisitos"] = lines
        return rep

    def create(self, validated_data):
        req_list = validated_data.pop("requisitos", [])
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


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for job applications"""

    candidate_info = serializers.SerializerMethodField()
    vacancy_info = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "vacancy",
            "candidate",
            "status",
            "applied_at",
            "notes",
            "candidate_info",
            "vacancy_info",
        ]
        read_only_fields = ("applied_at", "candidate_info", "vacancy_info")

    def get_candidate_info(self, obj):
        return {
            "id": obj.candidate.id,
            "email": obj.candidate.email,
            "name": obj.candidate.name,
        }

    def get_vacancy_info(self, obj):
        return {
            "id": obj.vacancy.id,
            "puesto": obj.vacancy.puesto,
            "company_name": obj.vacancy.company_name,
        }
