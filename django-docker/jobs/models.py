from django.db import models  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore
from django.utils import timezone  # type: ignore
import json

User = get_user_model()


class Vacante(models.Model):
    puesto = models.CharField(max_length=150)
    descripcion = models.TextField()
    requisitos = models.TextField(blank=True, default="")
    ubicacion = models.CharField(max_length=120)
    salariomin = models.CharField(max_length=100, blank=True, null=True)
    salariomax = models.CharField(max_length=100, blank=True, null=True)
    tipo_contrato = models.CharField(max_length=60, blank=True, null=True)
    activa = models.BooleanField(default=True)
    departamento = models.CharField(max_length=120, blank=True, default="")
    company_name = models.CharField(max_length=200, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vacantes_created",
    )

    generated_interview = models.JSONField(
        null=True, blank=True, help_text="Preguntas de entrevista generadas por IA"
    )

    def __str__(self):
        return f"{self.puesto} - {self.company_name or self.ubicacion}"

    @property
    def applications_count(self):
        """Number of candidates who applied"""
        return self.applications.count()


class Application(models.Model):
    """Relation between Candidate and Vacancy"""

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("reviewing", "En Revisión"),
        ("interview", "Entrevista"),
        ("accepted", "Aceptado"),
        ("rejected", "Rechazado"),
    ]

    vacancy = models.ForeignKey(
        Vacante, on_delete=models.CASCADE, related_name="applications"
    )
    candidate = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("vacancy", "candidate")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate.email} → {self.vacancy.puesto}"


class InterviewSession(models.Model):
    """Session for AI-conducted interviews"""

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("active", "Activa"),
        ("completed", "Completada"),
        ("abandoned", "Abandonada"),
    ]

    application = models.OneToOneField(
        "Application", on_delete=models.CASCADE, related_name="interview_session"
    )

    ai_session_id = models.CharField(max_length=100, blank=True, null=True)

    interview_config = models.JSONField(default=dict)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    current_question_index = models.IntegerField(default=0)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    total_score = models.FloatField(default=0.0)
    max_possible_score = models.FloatField(default=100.0)
    company_name = models.CharField(max_length=200, blank=True, default="")

    analysis_report = models.JSONField(
        null=True, blank=True, help_text="SWOT analysis report with quantitative score"
    )

    analyzed_at = models.DateTimeField(
        null=True, blank=True, help_text="When the analysis was generated"
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Interview {self.id} - {self.application.candidate.email}"

    def start_session(self, ai_session_id: str):
        """Mark session as started"""
        self.ai_session_id = ai_session_id
        self.status = "active"
        self.started_at = timezone.now()
        self.save()

    def complete_session(self):
        """Mark session as completed"""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()

    def is_active(self) -> bool:
        """Check if session is still active"""
        if self.status != "active":
            return False

        if self.last_activity:
            inactive_minutes = (
                timezone.now() - self.last_activity
            ).total_seconds() / 60
            if inactive_minutes > 30:
                self.status = "abandoned"
                self.save()
                return False

        return True

    def has_analysis(self) -> bool:
        """Check if the session has a generated analysis report"""
        return bool(self.analysis_report)

    def get_score_percentage(self) -> float:
        """
        Get the final score percentage.
        Returns the quantitative score from the analysis report if available,
        otherwise calculates the raw interview score percentage.
        """
        # If analyzed, return the comprehensive score (includes SWOT balance)
        if self.analysis_report and "quantitative_score" in self.analysis_report:
            return float(self.analysis_report.get("quantitative_score", 0.0))

        # Fallback: return raw interview score
        if self.max_possible_score > 0:
            return round((self.total_score / self.max_possible_score) * 100, 2)
        return 0.0


class ChatMessage(models.Model):
    """Individual chat messages in an interview session"""

    SENDER_CHOICES = [
        ("candidate", "Candidato"),
        ("ai", "IA"),
        ("system", "Sistema"),
    ]

    session = models.ForeignKey(
        InterviewSession, on_delete=models.CASCADE, related_name="messages"
    )

    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    content = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)
    question_index = models.IntegerField(null=True, blank=True)

    evaluation = models.JSONField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender} at {self.timestamp.strftime('%H:%M')}"
