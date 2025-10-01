from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Tuple
from uuid import uuid4
from ollama_client import chat_once

app = FastAPI(title="Evalyze AI Service")

# ===== memoria en RAM por sesión (simple para demo) =====
# { session_id: [("user msg", "assistant msg"), ...] }
SESSIONS: Dict[str, List[Tuple[str, str]]] = {}

SYSTEM = (
    "Eres un asistente para entrevistas/exámenes. "
    "Sé claro y conciso. Responde en español."
)

class StartReq(BaseModel):
    system: str | None = None
    model: str = "llama3"

class MsgReq(BaseModel):
    session_id: str
    text: str
    model: str = "llama3"

@app.get("/ping")
def ping():  # sanity check
    return {"ok": True}

@app.post("/chat/start")
def chat_start(req: StartReq):
    sid = str(uuid4())
    SESSIONS[sid] = []
    # warmup / primera respuesta
    system = req.system or SYSTEM
    first = chat_once(
        f"<system>{system}</system>\n<user>Inicia la conversación con un saludo breve.</user>\n<assistant>",
        model=req.model
    )
    SESSIONS[sid].append(("[start]", first))
    return {"session_id": sid, "message": first}

@app.post("/chat/message")
def chat_message(req: MsgReq):
    if req.session_id not in SESSIONS:
        raise HTTPException(404, "session not found")

    history = SESSIONS[req.session_id]
    # armamos un prompt corto con las últimas 2 interacciones
    turns = history[-2:]
    prompt = ["<system>"+SYSTEM+"</system>"]
    for (u,a) in turns:
        if u != "[start]":
            prompt.append(f"<user>{u}</user>\n<assistant>{a}</assistant>")
    prompt.append(f"<user>{req.text}</user>\n<assistant>")

    reply = chat_once("\n".join(prompt), model=req.model)
    history.append((req.text, reply))
    return {"message": reply, "turns": len(history)}
