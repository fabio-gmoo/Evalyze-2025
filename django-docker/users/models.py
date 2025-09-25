from django.db import models  # type: ignore
from django.contrib.auth.models import AbstractUser  # type: ignore


class Roles(models.TextChoices):
    COMPANY = "company", "Empresa"
    CANDIDATE = "candidate", "Candidato"


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.CANDIDATE
    )

    # Sugerencia: si no quieres usar username para login:
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # sigue existiendo, pero login por email

    def __str__(self):
        return f"{self.email} ({self.role})"


class CompanyProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="company_profile"
    )
    # Razón social / nombre comercial
    name = models.CharField(max_length=150)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=120, blank=True)
    # p.ej. 1-10, 11-50, etc.
    size = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"CompanyProfile({self.name})"


class CandidateProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="candidate_profile"
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=40, blank=True)
    location = models.CharField(max_length=120, blank=True)
    headline = models.CharField(max_length=200, blank=True)  # “Frontend dev…”
    # Campos opcionales:
    # resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    # skills = models.TextField(blank=True)

    def __str__(self):
        return f"CandidateProfile({self.full_name})"
