#!/usr/bin/env bash
set -e

# defaults
: "${AI_PROVIDER:=ollama}"
: "${OLLAMA_HOST:=http://ollama:11434}"
: "${OLLAMA_MODEL:=llama3.1}"

# si usamos ollama, espera y asegura el modelo
if [ "$AI_PROVIDER" = "ollama" ]; then
  echo "[ai-service] waiting for ollama at $OLLAMA_HOST ..."
  until curl -s "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; do sleep 1; done
  echo "[ai-service] ensuring model present: $OLLAMA_MODEL"
  curl -s -X POST "$OLLAMA_HOST/api/pull" -d "{\"name\":\"$OLLAMA_MODEL\"}" || true
fi

# arranca FastAPI (tu main.py está en /app)
exec python -m uvicorn main:app --host 0.0.0.0 --port 8080
