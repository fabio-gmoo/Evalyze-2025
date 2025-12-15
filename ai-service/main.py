from validate_exam import validate_exam
from rag_retrieve import Retriever
from ollama_client import chat_once
from validators import (
    validate_interview_questions,
    validate_response_evaluation,
    validate_swot_analysis,
    extract_json_from_text,
    sanitize_json_score,
)
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

    retriever: Optional[Retriever] = Retriever()
    HAS_RETRIEVER = True
    logger.info("✅ Retriever loaded successfully")
except Exception as e:
    retriever: Optional[Retriever] = None
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

SESSIONS: Dict[str, Dict] = {}


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


class EvaluateResponseReq(BaseModel):
    question: Dict
    candidate_response: str
    model: str = DEFAULT_EXAM_MODEL


class GenerateSWOTReq(BaseModel):
    vacancy_title: str
    level: str
    interview_data: Dict
    candidate_responses: List[Dict]
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

    return f"""INSTRUCCIONES CRÍTICAS - PARA LLAMA3.2:

Eres un experto en entrevistas técnicas para reclutamiento. Tu única tarea es generar ÚNICAMENTE JSON válido.

VACANTE: {vacancy_title}
NIVEL: {level}

REQUISITOS ESPECÍFICOS DEL PUESTO:
{reqs_text}

TAREA EXACTA:
Genera exactamente {n} preguntas de entrevista en formato JSON puro.

RESTRICCIONES OBLIGATORIAS:
1. SOLO devuelve JSON válido. CERO texto adicional antes o después.
2. La estructura DEBE ser exactamente este esquema:
{schema}

3. Cada pregunta DEBE tener:
   - id: "Q1", "Q2", etc.
   - question: Pregunta clara en español (máximo 150 caracteres)
   - type: SOLO uno de: "technical", "behavioral", "situational"
   - expected_keywords: Lista de palabras clave que indican una buena respuesta
   - rubric: Criterio de evaluación específico
   - weight: Número entero (25, 30, 20, etc). Total DEBE ser 100

4. Pesos OBLIGATORIOS según nivel:
   - junior: preguntas básicas, pesos 20-30 cada una
   - intermedio: experiencia práctica, pesos 20-30 cada una
   - senior: arquitectura/decisiones, pesos 25-30 cada una

5. Tipos de preguntas requeridas (por nivel):
   - junior: 60% technical, 30% behavioral, 10% situational
   - intermedio: 50% technical, 30% behavioral, 20% situational
   - senior: 40% technical, 30% behavioral, 30% situational

6. Enfoca TODAS las preguntas en los requisitos específicos listados arriba.

FORMATO DE EJEMPLO EXACTO:
{schema}

ACCIÓN FINAL:
Devuelve SOLO el JSON. Nada más. Sin comillas de bloque, sin explicaciones, sin comentarios.
"""


def build_response_evaluation_prompt(question: Dict, response: str) -> str:
    """
    Build prompt to evaluate a candidate's response to an interview question.
    Returns structured evaluation JSON.
    """
    return f"""EVALUACIÓN DE RESPUESTA - PARA LLAMA3.2

PREGUNTA:
{question.get('question', 'N/A')}

TIPO: {question.get('type', 'technical')}
PALABRAS CLAVE ESPERADAS: {', '.join(question.get('expected_keywords', []))}
RÚBRICA: {question.get('rubric', 'Respuesta general')}
PESO: {question.get('weight', 25)}%

RESPUESTA DEL CANDIDATO:
"{response}"

TAREA:
Evalúa la respuesta de forma OBJETIVA y genera JSON de evaluación.

CRITERIOS DE EVALUACIÓN:
1. Relevancia: ¿Responde la pregunta directamente? (0-100)
2. Completitud: ¿Cubre todos los aspectos importantes? (0-100)
3. Palabras clave: ¿Menciona palabras clave esperadas? (0-100)
4. Claridad: ¿Es clara y bien estructurada? (0-100)
5. Profundidad: ¿Muestra conocimiento profundo? (0-100)

ESTRUCTURA JSON OBLIGATORIA:
{{
    "question_id": "{question.get('id', 'Q1')}",
    "relevance_score": 85,
    "completeness_score": 80,
    "keywords_found": ["palabra1", "palabra2"],
    "keywords_missing": ["palabra3"],
    "clarity_score": 90,
    "depth_score": 75,
    "overall_score": 82,
    "strengths": ["Punto fuerte 1", "Punto fuerte 2"],
    "weaknesses": ["Punto débil 1", "Punto débil 2"],
    "feedback": "Análisis breve de la respuesta",
    "level_match": "junior|intermedio|senior"
}}

CÁLCULO OBLIGATORIO:
- overall_score = promedio de los 5 criterios redondeado
- Asegúrate que TODOS los campos sean numéricamente válidos
- Strings en arrays SOLO para strengths, weaknesses, keywords

ACCIÓN FINAL:
Devuelve SOLO el JSON válido. Sin explicaciones, sin texto adicional."""


def build_swot_analysis_prompt(vacancy_title: str, level: str, evaluations: List[Dict], n_questions: int) -> str:
    """
    Build prompt to generate SWOT analysis based on interview evaluations.
    SWOT = Strengths, Weaknesses, Opportunities, Threats
    """
    evaluations_text = json.dumps(evaluations, ensure_ascii=False, indent=2)
    
    return f"""ANÁLISIS SWOT - PARA LLAMA3.2

PUESTO: {vacancy_title}
NIVEL REQUERIDO: {level}
NÚMERO DE PREGUNTAS: {n_questions}

EVALUACIONES DE RESPUESTAS:
{evaluations_text}

TAREA:
Basándote ÚNICAMENTE en las evaluaciones anteriores, genera un análisis SWOT objetivo del candidato.

DEFINICIONES:
- FORTALEZAS: Puntos donde el candidato mostró conocimiento sólido (overall_score >= 75)
- DEBILIDADES: Áreas donde el candidato tuvo dificultades (overall_score < 70)
- OPORTUNIDADES: Áreas de crecimiento profesional identificadas
- AMENAZAS: Brechas críticas que podrían limitar desempeño

RESTRICCIONES CRÍTICAS:
1. SOLO menciona fortalezas si overall_score >= 75
2. SOLO menciona debilidades si overall_score < 70
3. Cada punto DEBE estar respaldado por datos de las evaluaciones
4. Máximo 5 puntos por sección (4 puntos recomendado)
5. NO inventes información que no esté en las evaluaciones

ESTRUCTURA JSON OBLIGATORIA:
{{
    "vacancy": "{vacancy_title}",
    "level": "{level}",
    "candidate_level": "junior|intermedio|senior",
    "overall_score": 78,
    "swot": {{
        "strengths": [
            {{"title": "Fortaleza 1", "description": "Descripción basada en datos", "score_reference": 85}},
            {{"title": "Fortaleza 2", "description": "Descripción basada en datos", "score_reference": 82}}
        ],
        "weaknesses": [
            {{"title": "Debilidad 1", "description": "Descripción basada en datos", "score_reference": 65}},
            {{"title": "Debilidad 2", "description": "Descripción basada en datos", "score_reference": 60}}
        ],
        "opportunities": [
            "Oportunidad de mejora 1",
            "Oportunidad de mejora 2"
        ],
        "threats": [
            "Brecha crítica 1",
            "Brecha crítica 2"
        ]
    }},
    "recommendation": "HIRE|INTERVIEW_AGAIN|REJECT",
    "rationale": "Explicación corta de la recomendación",
    "next_steps": ["Paso 1", "Paso 2"]
}}

REGLAS PARA RECOMENDACIÓN:
- HIRE: overall_score >= 75 Y candidate_level == required_level
- INTERVIEW_AGAIN: overall_score entre 65-74 O hay potencial
- REJECT: overall_score < 60 O brechas críticas

ACCIÓN FINAL:
Devuelve SOLO el JSON válido. Sin explicaciones, sin markdown, sin comillas de bloque."""


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
            "/evaluate_response",
            "/generate_swot_analysis",
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

    system = req.system
    SESSIONS[sid] = {"system": system, "history": []}
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
        raise HTTPException(
            status_code=502, detail=f"Ollama error (start): {e}")
    SESSIONS[sid]["history"].append(("[start]", first))
    return {"session_id": sid, "message": first}


@app.post("/chat/message")
def chat_message(req: MsgReq):
    if req.session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="session not found")

    session = SESSIONS[req.session_id]
    system = session["system"]
    history = session["history"]

    turns = history[:]
    prompt = [f"<system>{system}</system>"]
    for u, a in turns:
        if u != "[start]":
            prompt.append(f"<user>{u}</user>\n<assistant>{a}</assistant>")
    prompt.append(f"<user>{req.text}</user>\n<assistant>")

    try:
        reply = chat_once("\n".join(prompt), model=req.model)
    except Exception as e:
        logger.error(f"Error in chat_message: {e}")
        raise HTTPException(
            status_code=502, detail=f"Ollama error (message): {e}")

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

    assert retriever is not None

    # fmt:off
    query = f"{req.role} {req.level} examen preguntas opciones rúbrica SQL Node pagos"
    # fmt:on
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
    Optimizado para llama3.2 con validación estricta.
    """
    logger.info(f"Generating interview for: {req.vacancy_title}")

    prompt = build_interview_prompt(
        vacancy_title=req.vacancy_title,
        requirements=req.requirements,
        n=req.n_questions,
        level=req.level,
    )

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = chat_once(prompt, model=req.model)
            logger.info(f"Attempt {attempt + 1}: Got response from Ollama")

            # Extract JSON from response
            success, data = extract_json_from_text(response)
            
            if not success:
                raise ValueError("No JSON found in response")

            # Validate structure
            is_valid, error_msg = validate_interview_questions(data, req.n_questions)
            
            if is_valid:
                logger.info(f"✅ Interview generated successfully")
                return {"ok": True, "interview": data, "raw_response": response}
            else:
                raise ValueError(f"Invalid structure: {error_msg}")

        except Exception as parse_error:
            logger.warning(f"Attempt {attempt + 1} parse error: {parse_error}")
            
            if attempt < max_retries:
                # Retry with fix
                fix_prompt = f"""El JSON de preguntas de entrevista tiene errores. Corrígelo EXACTAMENTE según el esquema:

ERRORES A CORREGIR:
- Debe tener exactamente {req.n_questions} preguntas
- El total de "weight" debe ser 100
- Cada pregunta necesita: id, question, type, expected_keywords, rubric, weight
- Tipos válidos: technical, behavioral, situational

JSON INCORRECTO:
{response}

Devuelve SOLO el JSON corregido, sin explicaciones."""
                
                try:
                    response = chat_once(fix_prompt, model=req.model)
                    logger.info(f"Retry prompt sent for correction")
                except Exception as retry_error:
                    logger.error(f"Retry error: {retry_error}")
                    continue
            else:
                logger.error(f"Failed after {max_retries + 1} attempts")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate valid interview: {parse_error}"
                )

    raise HTTPException(status_code=502, detail="Ollama service error")


@app.post("/evaluate_response")
def evaluate_response(req: EvaluateResponseReq):
    """
    Evalúa la respuesta de un candidato a una pregunta específica.
    Retorna puntuaciones y retroalimentación detallada.
    """
    logger.info(f"Evaluating response for question: {req.question.get('id')}")

    prompt = build_response_evaluation_prompt(req.question, req.candidate_response)
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = chat_once(prompt, model=req.model)
            logger.info(f"Attempt {attempt + 1}: Got evaluation response")
            
            # Extract JSON
            success, evaluation = extract_json_from_text(response)
            
            if not success:
                raise ValueError("No JSON found in response")
            
            # Validate structure
            is_valid, error_msg = validate_response_evaluation(evaluation)
            
            if not is_valid:
                raise ValueError(f"Invalid structure: {error_msg}")
            
            # Sanitize scores
            score_fields = [
                "overall_score", "relevance_score", "completeness_score",
                "clarity_score", "depth_score"
            ]
            evaluation = sanitize_json_score(evaluation, score_fields)
            
            logger.info(f"✅ Response evaluated successfully. Score: {evaluation['overall_score']}")
            return {
                "ok": True,
                "evaluation": evaluation,
                "raw_response": response
            }
                
        except Exception as parse_error:
            logger.warning(f"Attempt {attempt + 1} parse error: {parse_error}")
            
            if attempt < max_retries:
                # Retry with explicit fix
                fix_prompt = f"""La evaluación de respuesta tiene errores. Corrígela con este esquema JSON exacto:

{{
    "question_id": "ID de pregunta",
    "relevance_score": 85,
    "completeness_score": 80,
    "keywords_found": ["palabra1"],
    "keywords_missing": ["palabra2"],
    "clarity_score": 90,
    "depth_score": 75,
    "overall_score": 82,
    "strengths": ["Punto fuerte"],
    "weaknesses": ["Punto débil"],
    "feedback": "Análisis breve",
    "level_match": "junior"
}}

Respuesta incorrecta a corregir:
{response}

Devuelve SOLO el JSON válido."""
                
                try:
                    response = chat_once(fix_prompt, model=req.model)
                    logger.info(f"Retry sent for evaluation fix")
                except Exception as retry_error:
                    logger.error(f"Retry error: {retry_error}")
                    continue
            else:
                logger.error(f"Failed to evaluate after {max_retries + 1} attempts")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to evaluate response: {parse_error}"
                )
    
    raise HTTPException(status_code=502, detail="Ollama service error")


@app.post("/generate_swot_analysis")
def generate_swot_analysis(req: GenerateSWOTReq):
    """
    Genera un análisis SWOT basado en las evaluaciones de respuestas.
    Los datos DEBEN estar respaldados por evaluaciones numéricas.
    """
    logger.info(f"Generating SWOT analysis for: {req.vacancy_title}")
    
    if not req.candidate_responses:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate SWOT without candidate responses"
        )
    
    # Prepare evaluations data
    evaluations = []
    total_score = 0
    
    for i, resp in enumerate(req.candidate_responses):
        eval_data = {
            "question_id": resp.get("question_id", f"Q{i+1}"),
            "overall_score": resp.get("overall_score", 50),
            "feedback": resp.get("feedback", ""),
            "strengths": resp.get("strengths", []),
            "weaknesses": resp.get("weaknesses", [])
        }
        evaluations.append(eval_data)
        total_score += eval_data["overall_score"]
    
    avg_score = round(total_score / len(evaluations)) if evaluations else 0
    
    prompt = build_swot_analysis_prompt(
        req.vacancy_title,
        req.level,
        evaluations,
        len(req.candidate_responses)
    )
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = chat_once(prompt, model=req.model)
            logger.info(f"Attempt {attempt + 1}: Got SWOT response")
            
            # Extract JSON
            success, analysis = extract_json_from_text(response)
            
            if not success:
                raise ValueError("No JSON found in response")
            
            # Validate structure
            is_valid, error_msg = validate_swot_analysis(analysis)
            
            if not is_valid:
                raise ValueError(f"Invalid structure: {error_msg}")
            
            # Set overall score from evaluations if not present
            if "overall_score" not in analysis or analysis["overall_score"] is None:
                analysis["overall_score"] = avg_score
            
            logger.info(f"✅ SWOT analysis generated. Overall score: {analysis.get('overall_score', 0)}")
            return {
                "ok": True,
                "analysis": analysis,
                "raw_response": response
            }
                
        except Exception as parse_error:
            logger.warning(f"Attempt {attempt + 1} parse error: {parse_error}")
            
            if attempt < max_retries:
                # Retry with explicit structure
                fix_prompt = f"""El análisis SWOT tiene errores. Corrígelo con exactamente esta estructura:

{{
    "vacancy": "nombre del puesto",
    "level": "nivel requerido",
    "candidate_level": "nivel del candidato",
    "overall_score": {avg_score},
    "swot": {{
        "strengths": [
            {{"title": "Fortaleza", "description": "Descripción", "score_reference": 80}}
        ],
        "weaknesses": [
            {{"title": "Debilidad", "description": "Descripción", "score_reference": 60}}
        ],
        "opportunities": ["Oportunidad 1"],
        "threats": ["Amenaza 1"]
    }},
    "recommendation": "HIRE",
    "rationale": "Explicación",
    "next_steps": ["Paso 1"]
}}

Datos incorrecto a corregir:
{response}

Devuelve SOLO el JSON válido."""
                
                try:
                    response = chat_once(fix_prompt, model=req.model)
                    logger.info(f"Retry sent for SWOT fix")
                except Exception as retry_error:
                    logger.error(f"Retry error: {retry_error}")
                    continue
            else:
                logger.error(f"Failed SWOT generation after {max_retries + 1} attempts")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate SWOT analysis"
                )
    
    raise HTTPException(status_code=502, detail="Ollama service error")
