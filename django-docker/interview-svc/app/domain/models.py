from pydantic import BaseModel, Field, field_validator  # type: ignore


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
    descripcion_sugerida: str
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
