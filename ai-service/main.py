from validate_exam import validate_exam
from rag_retrieve import Retriever
from ollama_client import chat_once
from fastapi import FastAPI, HTTPException  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import Dict, List, Tuple, Optional
from uuid import uuid4
import subprocess
import sys
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    from rag_retrieve import Retriever

    retriever = Retriever()
    HAS_RETRIEVER = True
    logger.info("✅ Retriever loaded successfully")
except Exception as e:
    retriever = None
    HAS_RETRIEVER = False
    logger.warning(f"⚠️ Retriever not available: {e}")


app = FastAPI(title="Evalyze AI Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: Dict[str, List[Tuple[str, str]]] = {}
SYSTEM = (
    "Eres **Evalyze Assistant**, el asistente oficial de la plataforma Evalyze. "
    "Preséntate como 'Evalyze Assistant' al iniciar. "
    "Ayudas a crear y revisar entrevistas/exámenes técnicos. "
    "Sé claro, profesional y breve. Responde en español."
)

# Use a model that should be available
DEFAULT_CHAT_MODEL = "llama3.2"
DEFAULT_EXAM_MODEL = "llama3.2"

# Rest of your classes...


class StartReq(BaseModel):
    system: Optional[str] = None
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


class GenerateInterviewReq(BaseModel):
    vacancy_title: str
    requirements: List[str]
    level: str = "intermedio"
    n_questions: int = 4
    model: str = DEFAULT_EXAM_MODEL


# Your functions...


def build_exam_prompt(ctx: str, role: str, n: int, level: str) -> str:
    schema = f'''{{
    "title": "Examen {role}",
    "meta": {{"level":"{level}","count":{n}}},
    "questions": [
    {{"id":"ED-001","q":"texto","options":["A","B","C","D"],
        "answer":"A","why":"(si procede)","rubrics":["SQL/optimización"]}}
    ]
    }}'''
    return f"""
    CONTEXT:
    ---
    {ctx}
    ---

    EXAM:
    Genera un examen de {n} preguntas para la vacante {role}, nivel {level}.
    - Usa SOLO el CONTEXT.
    - Cubre criterios de la rúbrica del rol.
    - Si level=intermedio: 30% fácil, 50% intermedio, 20% avanzado.
    - Devuelve SOLO el JSON exacto con este esquema:
    {schema}
    """


def build_interview_prompt(
    vacancy_title: str, requirements: List[str], n: int, level: str
) -> str:
    reqs_text = "\n".join(f"- {r}" for r in requirements)

    schema = """{
    "vacancy": "título del puesto",
    "level": "junior|intermedio|senior",
    "questions": [
    {
      "id": "Q1",
      "question": "Pregunta técnica o de experiencia",
      "type": "technical|behavioral|situational",
      "expected_keywords": ["palabra1", "palabra2"],
      "rubric": "criterio de evaluación",
      "weight": 25
    }
  ]
}"""

    return f"""
    Eres un experto en entrevistas técnicas para reclutamiento.

    VACANTE: {vacancy_title}
    NIVEL: {level}

    REQUISITOS:
    {reqs_text}

    TAREA:
    Genera {n} preguntas de entrevista para evaluar si el candidato cumple con los requisitos.

    CRITERIOS:
    - Preguntas claras y directas en español
    - Mezcla de tipos: técnicas (50%), conductuales (30%), situacionales (20%)
    - Enfocadas en los requisitos específicos
    - Incluye palabras clave esperadas en la respuesta
    - Asigna peso según importancia (total 100%)

    NIVEL {level}:
    - junior: preguntas básicas de conceptos y fundamentos
    - intermedio: experiencia práctica y resolución de problemas
    - senior: arquitectura, liderazgo y decisiones estratégicas

    Devuelve ÚNICAMENTE el JSON con este esquema exacto:
    {schema}

    NO incluyas texto adicional, solo el JSON.
    """


@app.get("/")
def root():
    return {
        "service": "Evalyze AI",
        "status": "running",
        "has_retriever": HAS_RETRIEVER,
        "default_model": DEFAULT_CHAT_MODEL,
        "endpoints": [
            "/healthz",
            "/ping",
            "/ollama/status",
            "/chat/start",
            "/chat/message",
            "/reindex",
            "/generate_exam",
            "/generate_interview",
            "/docs",
        ],
    }


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.get("/ping")
def ping():
    return {"ok": True, "has_retriever": HAS_RETRIEVER}


@app.get("/ollama/status")
def ollama_status():
    """Check if Ollama is running and which models are available"""
    try:
        import requests

        ollama_url = "http://ollama:11434/api/tags"
        response = requests.get(ollama_url, timeout=5)

        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "ok": True,
                "available_models": [m["name"] for m in models],
                "default_model": DEFAULT_CHAT_MODEL,
            }
        else:
            return {"ok": False, "error": "Ollama not responding"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/chat/start")
def chat_start(req: StartReq):
    sid = str(uuid4())
    SESSIONS[sid] = []
    system = req.system or SYSTEM
    # fmt:off
    prompt = f"<system>{system}</system>\n<user>Inicia la conversación con un saludo breve.</user>\n<assistant>"
    # fmt: on
    try:
        first = chat_once(
            prompt,
            model=req.model,
        )
    except Exception as e:
        logger.error(f"Error in chat_start: {e}")
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
    for u, a in turns:
        if u != "[start]":
            prompt.append(f"<user>{u}</user>\n<assistant>{a}</assistant>")
    prompt.append(f"<user>{req.text}</user>\n<assistant>")
    try:
        reply = chat_once("\n".join(prompt), model=req.model)
    except Exception as e:
        logger.error(f"Error in chat_message: {e}")
        raise HTTPException(status_code=502, detail=f"Ollama error (message): {e}")
    history.append((req.text, reply))
    return {"message": reply, "turns": len(history)}


@app.post("/reindex")
def reindex(_: Empty):
    if not HAS_RETRIEVER:
        raise HTTPException(status_code=503, detail="Retriever not available")

    out = subprocess.run(
        [sys.executable, "rag_index.py"], capture_output=True, text=True
    )
    global retriever
    retriever = Retriever()
    return {"stdout": out.stdout, "stderr": out.stderr}


@app.post("/generate_exam")
def generate_exam(req: GenerateExamReq):
    if not HAS_RETRIEVER:
        raise HTTPException(
            status_code=503,
            detail="Retriever not available. Cannot generate exam without knowledge base.",
        )

    query = f"{req.role} {req.level} examen preguntas opciones rúbrica SQL Node pagos"
    ctx = "\n\n".join(d["text"] for d in retriever.topk(query, 6))
    prompt = build_exam_prompt(ctx, req.role, req.n, req.level)
    try:
        out = chat_once(prompt, model=req.model)
    except Exception as e:
        logger.error(f"Error in generate_exam: {e}")
        raise HTTPException(
            status_code=502, detail=f"Ollama error (generate_exam): {e}"
        )
    val = validate_exam(out)
    if not val["ok"]:
        # fmt:off
        fix = f"Corrige este JSON al esquema exacto, sin texto fuera del JSON.\n\n{out}\n\nESQUEMA:\n{build_exam_prompt(ctx, req.role, req.n, req.level)}"
        # fmt: on
        out = chat_once(fix, model=req.model)
        val = validate_exam(out)
    return {"ok": val["ok"], "exam": out, "validation": val}


@app.post("/generate_interview")
def generate_interview(req: GenerateInterviewReq):
    """
    Genera preguntas de entrevista basadas en los requisitos de la vacante.
    """
    logger.info(f"Generating interview for: {req.vacancy_title}")

    prompt = build_interview_prompt(
        vacancy_title=req.vacancy_title,
        requirements=req.requirements,
        n=req.n_questions,
        level=req.level,
    )

    try:
        response = chat_once(prompt, model=req.model)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

            if not isinstance(data.get("questions"), list):
                raise ValueError("'questions' must be a list")

            if len(data["questions"]) < req.n_questions:
                raise ValueError(
                    # fmt:off
                    f"Expected {req.n_questions} questions, got {len(data['questions'])}"
                    # fmt:on
                )

            for i, q in enumerate(data["questions"], 1):
                if not q.get("question"):
                    raise ValueError(f"Question {i} missing 'question' field")
                if not q.get("type"):
                    raise ValueError(f"Question {i} missing 'type' field")
                if not isinstance(q.get("expected_keywords"), list):
                    raise ValueError(f"Question {i} missing 'expected_keywords' list")

            logger.info(f"✅ Interview generated successfully")
            return {"ok": True, "interview": data, "raw_response": response}

        except Exception as parse_error:
            logger.warning(f"Parse error, attempting fix: {parse_error}")
            fix_prompt = f"""
                El siguiente JSON tiene errores. Corrígelo para que sea válido:

                {response}

                Devuelve ÚNICAMENTE el JSON corregido, sin texto adicional.
            """
            try:
                fixed = chat_once(fix_prompt, model=req.model)
                start = fixed.find("{")
                end = fixed.rfind("}") + 1
                json_str = fixed[start:end]
                data = json.loads(json_str)

                return {
                    "ok": True,
                    "interview": data,
                    "raw_response": fixed,
                    "was_fixed": True,
                }
            except Exception as fix_error:
                logger.error(f"Failed to fix JSON: {fix_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse interview response: {parse_error}",
                )

    except Exception as e:
        logger.error(f"Error in generate_interview: {e}")
        raise HTTPException(
            status_code=502, detail=f"Ollama error (generate_interview): {str(e)}"
        )
