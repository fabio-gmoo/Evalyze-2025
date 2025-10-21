from django.contrib.auth import get_user_model, authenticate  # type: ignore
from django.contrib.auth.password_validation import validate_password  # type:ignore
from rest_framework import serializers  # type: ignore

from .models import Roles, CompanyProfile, CandidateProfile

User = get_user_model()

# === Base ===


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "role", "name")


# === Registro de Empresa ===


class RegisterCompanySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm = serializers.CharField(write_only=True)
    # Campos del perfil:
    company_name = serializers.CharField(write_only=True)
    size = serializers.CharField(required=False, allow_blank=True, write_only=True)
    country = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "confirm",
            "company_name",
            "size",
            "country",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm"]:
            raise serializers.ValidationError(
                {"confirm": "Las contraseñas no coinciden"}
            )
        validate_password(attrs["password"])
        return attrs

    def create(self, data):
        pwd = data.pop("password")
        data.pop("confirm")
        company_name = data.pop("company_name")

        size = data.pop("size", "")
        country = data.pop("country", "")

        user = User(email=data["email"], role=Roles.COMPANY, username=data["email"])
        user.set_password(pwd)
        user.save()

        CompanyProfile.objects.create(
            user=user,
            company_name=company_name,
            size=size,
            country=country,
        )
        return user


# === Registro de Candidato ===


class RegisterCandidateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm = serializers.CharField(write_only=True)
    # Perfil:
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "confirm",
            "full_name",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm"]:
            raise serializers.ValidationError(
                {"confirm": "Las contraseñas no coinciden"}
            )
        validate_password(attrs["password"])
        return attrs

    def create(self, data):
        pwd = data.pop("password")
        data.pop("confirm")
        full_name = data.pop("full_name")

        user = User(email=data["email"], role=Roles.CANDIDATE, username=data["email"])
        user.set_password(pwd)
        user.save()

        CandidateProfile.objects.create(
            user=user,
            full_name=full_name,
        )
        return user
