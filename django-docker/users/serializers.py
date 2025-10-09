from django.contrib.auth import get_user_model, authenticate  # type: ignore
from django.contrib.auth.password_validation import validate_password  # type:ignore
from rest_framework import serializers  # type: ignore

from .models import Roles, CompanyProfile, CandidateProfile

User = get_user_model()

# === Base ===


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role")


# === Registro de Empresa ===


class RegisterCompanySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm = serializers.CharField(write_only=True)
    # Campos del perfil:
    company_name = serializers.CharField(write_only=True)
    website = serializers.URLField(required=False, allow_blank=True, write_only=True)
    industry = serializers.CharField(required=False, allow_blank=True, write_only=True)
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
            "website",
            "industry",
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
        website = data.pop("website", "")
        industry = data.pop("industry", "")
        size = data.pop("size", "")
        country = data.pop("country", "")

        user = User(email=data["email"], role=Roles.COMPANY, username=data["email"])
        user.set_password(pwd)
        user.save()

        CompanyProfile.objects.create(
            user=user,
            name=company_name,
            website=website,
            industry=industry,
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
    phone = serializers.CharField(required=False, allow_blank=True, write_only=True)
    location = serializers.CharField(required=False, allow_blank=True, write_only=True)
    headline = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "confirm",
            "full_name",
            "phone",
            "location",
            "headline",
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
        phone = data.pop("phone", "")
        location = data.pop("location", "")
        headline = data.pop("headline", "")

        user = User(email=data["email"], role=Roles.CANDIDATE, username=data["email"])
        user.set_password(pwd)
        user.save()

        CandidateProfile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            location=location,
            headline=headline,
        )
        return user
