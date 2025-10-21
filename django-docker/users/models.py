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

    @property
    def name(self):
        """
        Return the company’s name if the user is a company,
        or the candidate’s full name if the user is a candidate.
        """
        if hasattr(self, "company_profile"):
            return self.company_profile.company_name
        if hasattr(self, "candidate_profile"):
            return self.candidate_profile.full_name
        return ""


class CompanyProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="company_profile"
    )
    # Razón social / nombre comercial
    company_name = models.CharField(max_length=150)

    # p.ej. 1-10, 11-50, etc.
    size = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"CompanyProfile({self.company_name})"


class CandidateProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="candidate_profile"
    )
    full_name = models.CharField(max_length=150)

    def __str__(self):
        return f"CandidateProfile({self.full_name})"
