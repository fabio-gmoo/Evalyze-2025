import json
from typing import Any, Dict, List

def validate_exam(json_text: str) -> Dict[str, Any]:
    try:
        data = json.loads(json_text)
    except Exception as e:
        return {"ok": False, "error": f"JSON inválido: {e}"}

    qs: List[Dict[str, Any]] = data.get("questions")  # type: ignore
    if not isinstance(qs, list) or not qs:
        return {"ok": False, "error": "Debe tener 'questions' como lista no vacía."}

    for i, q in enumerate(qs, 1):
        if not isinstance(q, dict):
            return {"ok": False, "error": f"Cada pregunta debe ser un objeto (item {i})."}

        # enunciado
        if not q.get("q"):
            return {"ok": False, "error": f"'q' vacío en item {i}"}

        # opciones
        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) < 4:
            return {"ok": False, "error": f"'options' >= 4 en item {i}"}
        # evitar duplicados (normalizando a str por las dudas)
        if len(set(map(str, opts))) != len(opts):
            return {"ok": False, "error": f"'options' contiene duplicados en item {i}"}

        # respuesta
        ans = q.get("answer")
        if ans not in opts:
            return {"ok": False, "error": f"'answer' no está en 'options' en item {i}"}

    return {"ok": True, "count": len(qs)}
