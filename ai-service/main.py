from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Tuple
from uuid import uuid4
import subprocess, sys

# --- internos ---
from ollama_client import chat_once
from rag_retrieve import Retriever
from validate_exam import validate_exam

app = FastAPI(title="Evalyze AI Service")

# CORS para Angular local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== memoria en RAM por sesión (simple para demo) =====
# { session_id: [("user msg", "assistant msg"), ...] }
SESSIONS: Dict[str, List[Tuple[str, str]]] = {}

SYSTEM = (
    "Eres un asistente para entrevistas/exámenes. "
    "Sé claro y conciso. Responde en español."
)

# ===== RAG: cargamos el retriever (indexa con /reindex) =====
retriever = Retriever()

# ====== MODELOS por defecto ======
DEFAULT_CHAT_MODEL = "examiner"     # tu perfil de Modelfile (usa 'llama3' si aún no lo creaste)
DEFAULT_EXAM_MODEL = "examiner"


# ------------------ helpers ------------------

def build_exam_prompt(ctx: str, role: str, n: int, level: str) -> str:
    """Construye el prompt para pedir un examen en JSON estricto."""
    schema = f"""{{
  "title": "Examen {role}",
  "meta": {{"level":"{level}","count":{n}}},
  "questions": [
    {{
      "id": "ED-001",
      "q": "texto de la pregunta",
      "options": ["A","B","C","D"],
      "answer": "A",
      "why": "(solo si procede y está en el CONTEXT)",
      "rubrics": ["SQL/optimización"]
    }}
  ]
}}"""

    return f"""
CONTEXT:
---
{ctx}
---

EXAM:
Genera un examen de {n} preguntas para la vacante {role}, nivel {level}.
- Usa SOLO el CONTEXT.
- Cubre criterios de la rúbrica del rol.
- Si level = intermedio: 30% fácil, 50% intermedio, 20% avanzado.
- Devuelve SOLO el JSON y que cumpla EXACTAMENTE este esquema:
{schema}
"""


# ------------------ modelos de request ------------------

class StartReq(BaseModel):
    system: str | None = None
    model: str = DEFAULT_CHAT_MODEL

class MsgReq(BaseModel):
    session_id: str
    text: str
    model: str = DEFAULT_CHAT_MODEL

class Empty(BaseModel):
    pass

class GenerateExamReq(BaseModel):
    role: str
    n: int = 8
    level: str = "intermedio"
    model: str = DEFAULT_EXAM_MODEL


# ------------------ endpoints básicos ------------------

@app.get("/")
def root():
    return {
        "service": "Evalyze AI",
        "endpoints": ["/ping", "/chat/start", "/chat/message", "/reindex", "/generate_exam", "/docs"]
    }

@app.get("/ping")
def ping():
    return {"ok": True}


# ------------------ chat ------------------

@app.post("/chat/start")
def chat_start(req: StartReq):
    sid = str(uuid4())
    SESSIONS[sid] = []
    system = req.system or SYSTEM
    try:
        first = chat_once(
            f"<system>{system}</system>\n<user>Inicia la conversación con un saludo breve.</user>\n<assistant>",
            model=req.model
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error (start): {e}")
    SESSIONS[sid].append(("[start]", first))
    return {"session_id": sid, "message": first}

@app.post("/chat/message")
def chat_message(req: MsgReq):
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")

    history = SESSIONS[req.session_id]
    turns = history[-2:]
    prompt = [f"<system>{SYSTEM}</system>"]
    for (u, a) in turns:
        if u != "[start]":
            prompt.append(f"<user>{u}</user>\n<assistant>{a}</assistant>")
    prompt.append(f"<user>{req.text}</user>\n<assistant>")

    try:
        reply = chat_once("\n".join(prompt), model=req.model)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error (message): {e}")

    history.append((req.text, reply))
    return {"message": reply, "turns": len(history)}


# ------------------ RAG / indexado ------------------

@app.post("/reindex")
def reindex(_: Empty):
    """Reconstruye el índice de la KB (correr tras cambiar archivos en /kb)."""
    out = subprocess.run([sys.executable, "rag_index.py"], capture_output=True, text=True)
    # recarga el retriever en memoria
    global retriever
    retriever = Retriever()
    return {"stdout": out.stdout, "stderr": out.stderr}


# ------------------ generar examen ------------------

@app.post("/generate_exam")
def generate_exam(req: GenerateExamReq):
    # 1) RAG: construir contexto con top-K chunks
    query = f"{req.role} {req.level} examen preguntas opciones rúbrica SQL Node pagos testing"
    ctx_chunks = retriever.topk(query, k=6)
    ctx = "\n\n".join(d["text"] for d in ctx_chunks) if ctx_chunks else "N/A"

    # 2) Prompt y generación
    prompt = build_exam_prompt(ctx, req.role, req.n, req.level)

    try:
        out = chat_once(prompt, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error (generate_exam): {e}")

    # 3) Validación JSON; si falla, intentamos autocorregir una vez
    val = validate_exam(out)
    if not val["ok"]:
        fix_prompt = f"""Corrige este JSON para que cumpla EXACTAMENTE el esquema. No agregues texto fuera del JSON.

JSON_ORIGINAL:
{out}

ESQUEMA:
{build_exam_prompt(ctx, req.role, req.n, req.level)}
"""
        try:
            out = chat_once(fix_prompt, model=req.model)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Ollama error (fix JSON): {e}")
        val = validate_exam(out)

    return {"ok": val["ok"], "exam": out, "validation": val}
