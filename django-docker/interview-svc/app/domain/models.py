# interview-svc/app/domain/models.py
from pydantic import BaseModel, Field, field_validator  # type: ignore
from typing import List, Any


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # opcional


class VacancyDraftIn(BaseModel):
    puesto: str = Field(..., min_length=2)
    descripcion: str = Field(..., min_length=10)
    ubicacion: str = Field(..., min_length=2)
    salario: str | None = None
    tipo_contrato: str | None = None


# ======= OUTPUT: propuesta de IA (usuario puede editar) =======
class VacancyDraftOut(BaseModel):
    puesto: str
    descripcion_sugerida: str | None = None
    requisitos_sugeridos: list[str]

    @field_validator("requisitos_sugeridos", mode="before")
    @classmethod
    def _ensure_list(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # separar por saltos de línea o por punto/coma
            parts = [p.strip("-• ").strip()
                     for p in v.split("\n") if p.strip()]
            if parts:
                return parts
        return []


class ChatResponse(BaseModel):
    reply: str


class InterviewQuestion(BaseModel):
    id: str = Field(..., min_length=1)
    question: str
    type: str
    expected_keywords: List[str]
    rubric: str
    weight: int


class CandidateConversationStart(BaseModel):
    id: int  # Candidate ID
    email: str
    name: str


class StartConversationReq(BaseModel):
    vacancy_id: int
    vacancy_title: str
    # The core interview structure
    interview_questions: List[InterviewQuestion]
    candidates: List[CandidateConversationStart]


# NEW: Response model for conversation initiation
class StartConversationRes(BaseModel):
    status: str
    total_candidates: int
    started_chats: List[int]  # List of candidate IDs whose chats were started
