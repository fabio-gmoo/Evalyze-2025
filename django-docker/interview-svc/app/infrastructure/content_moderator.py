# interview-svc/app/infrastructure/content_moderator.py
"""
Moderador de contenido híbrido:
- OpenAI Moderation API (opcional)
- Google Perspective API (opcional)
- Filtro local (si los servicios están ausentes o fallan)

Objetivo: Nunca reventar por faltas de claves/librerías/red. Siempre devolver un resultado.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

# Dependencias opcionales; no deben romper en import.
# httpx y dotenv son usuales, pero si faltan, el módulo sigue funcionando con el filtro local.
try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore

# Cargar .env si está disponible (no es obligatorio)
if load_dotenv:
    try:
        load_dotenv()
    except Exception:
        pass

# Logging seguro (evita "No handler found" en algunos entornos)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentModerationResult:
    """Resultado de moderación"""

    def __init__(
        self,
        allowed: bool,
        flagged: bool,
        detail: str,
        categories: Optional[List[str]] = None,
        confidence: str = "unknown",
        sources: Optional[List[str]] = None,
    ):
        self.allowed = bool(allowed)
        self.flagged = bool(flagged)
        self.detail = detail or ""
        self.categories = categories or []
        self.confidence = confidence or "unknown"
        self.sources = sources or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "flagged": self.flagged,
            "detail": self.detail,
            "categories": self.categories,
            "confidence": self.confidence,
            "sources": self.sources,
        }


class HybridContentModerator:
    """
    Moderador híbrido: intenta servicios externos, cae a filtro local si no están disponibles.

    Parámetros env (opcionales):
      - PROVIDER_API_KEY
      - PROVIDER_BASE_URL (default: https://api.openai.com)
      - PROVIDER_MODERATION_MODEL (default: omni-moderation-latest)
      - PERSPECTIVE_API_KEY
    """

    def __init__(self, enable_local_fallback: bool = True):
        # OpenAI config
        self.openai_api_key = os.getenv("PROVIDER_API_KEY") or ""
        self.openai_base_url = (
            os.getenv("PROVIDER_BASE_URL") or "https://api.openai.com"
        ).rstrip("/")
        self.openai_model = (
            os.getenv("PROVIDER_MODERATION_MODEL") or "omni-moderation-latest"
        )
        self._openai_available = bool(self.openai_api_key and httpx is not None)

        # Perspective config (lazy init)
        self.perspective_api_key = os.getenv("PERSPECTIVE_API_KEY") or ""
        self._perspective_available = False
        self._perspective_client = None

        if self.perspective_api_key:
            try:
                # Lazy import para no romper si la lib no existe
                from googleapiclient.discovery import build  # type: ignore

                self._perspective_client = build(
                    "commentanalyzer",
                    "v1alpha1",
                    developerKey=self.perspective_api_key,
                    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
                    static_discovery=False,
                )
                self._perspective_available = True
                logger.info("✅ Perspective API inicializada")
            except Exception as e:
                self._perspective_client = None
                self._perspective_available = False
                logger.warning(f"⚠️ Perspective API no disponible: {e}")

        self.enable_local_fallback = bool(enable_local_fallback)

        # Compilar reglas locales (rápidas, sin dependencias)
        self._local_rules: List[Tuple[str, re.Pattern]] = self._build_local_rules()

    # -----------------------------
    # Interfaz pública
    # -----------------------------
    def moderate(
        self,
        text: str,
        require_consensus: bool = False,
        perspective_threshold: float = 0.7,
    ) -> ContentModerationResult:
        """Modera texto; siempre retorna un resultado válido."""
        safe_text = text or ""
        logger.info(f"🔍 Moderando contenido: {safe_text[:50]}...")

        sources: List[str] = []
        openai_result = {"service": "openai", "flagged": None, "detail": "No usado"}
        perspective_result = {
            "service": "perspective",
            "flagged": None,
            "detail": "No usado",
        }

        # 1) OpenAI si está disponible
        if self._openai_available:
            openai_result = self._check_openai(safe_text)
            sources.append("openai")

            # Si OpenAI rechaza y no exigimos consenso, atajar aquí
            if openai_result.get("flagged") is True:
                if not require_consensus:
                    return ContentModerationResult(
                        allowed=False,
                        flagged=True,
                        detail=openai_result.get("detail", "Rechazado por OpenAI"),
                        categories=openai_result.get("categories", []),
                        confidence="high",
                        sources=sources,
                    )

        # 2) Perspective si está disponible
        if self._perspective_available and self._perspective_client:
            perspective_result = self._check_perspective(
                safe_text, perspective_threshold
            )
            sources.append("perspective")

            # Si Perspective rechaza exitosamente (no error)
            if perspective_result.get("flagged") is True:
                if not require_consensus:
                    return ContentModerationResult(
                        allowed=False,
                        flagged=True,
                        detail=perspective_result.get(
                            "detail", "Rechazado por Perspective"
                        ),
                        categories=perspective_result.get("categories", []),
                        confidence="high",
                        sources=sources,
                    )

        openai_approved = openai_result.get("flagged") is False
        perspective_approved = perspective_result.get("flagged") is False

        if openai_approved and perspective_approved:
            return ContentModerationResult(
                allowed=True,
                flagged=False,
                detail="Aprobado por servicios externos",
                confidence="high",
                sources=sources,
            )

        # 4) Si llegamos aquí, al menos un servicio falló o ninguno se usó
        #    → USAR FILTRO LOCAL OBLIGATORIAMENTE
        if self.enable_local_fallback:
            logger.warning(
                "⚠️ Servicios externos no disponibles o fallaron. Usando filtro local."
            )
            local = self._check_local(safe_text)
            local.sources = sources + ["local"]
            return local
        # 5) Sin servicios y sin fallback → RECHAZAR por seguridad
        logger.error(
            "❌ Sin servicios disponibles y sin fallback local. RECHAZANDO por defecto."
        )
        return ContentModerationResult(
            allowed=False,  # ← CRÍTICO: Rechazar en caso de duda
            flagged=True,
            detail="No se pudo verificar el contenido (servicios no disponibles)",
            confidence="none",
            sources=sources or ["none"],
        )

    # -----------------------------
    # OpenAI
    # -----------------------------
    def _check_openai(self, text: str) -> Dict[str, Any]:
        if not self._openai_available or not httpx:
            return {
                "service": "openai",
                "flagged": None,
                "detail": "OpenAI no disponible",
            }

        url = f"{self.openai_base_url}/v1/moderations"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"input": text, "model": self.openai_model}

        try:
            with httpx.Client(timeout=30.0) as client:  # type: ignore
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.error(f"❌ Error OpenAI Moderation: {e}")
            return {
                "service": "openai",
                "flagged": None,
                "detail": f"Error OpenAI: {e}",
            }

        result = (data.get("results") or [{}])[0]
        flagged = bool(result.get("flagged", False))
        categories_dict = result.get("categories") or {}
        scores = result.get("category_scores") or result.get("scores") or {}

        flagged_categories = [
            self._format_category(cat)
            for cat, is_flagged in categories_dict.items()
            if bool(is_flagged)
        ]
        severity = self._calculate_severity(scores if isinstance(scores, dict) else {})

        return {
            "service": "openai",
            "flagged": flagged,
            "categories": flagged_categories,
            "scores": scores,
            "severity": severity,
            "detail": "OpenAI detectó: " + ", ".join(flagged_categories)
            if flagged_categories
            else ("OpenAI marcó el contenido" if flagged else "Aprobado por OpenAI"),
        }

    # -----------------------------
    # Perspective
    # -----------------------------
    def _check_perspective(self, text: str, threshold: float) -> Dict[str, Any]:
        if not (self._perspective_available and self._perspective_client):
            return {
                "service": "perspective",
                "flagged": None,
                "detail": "Perspective no disponible",
            }

        analyze_request = {
            "comment": {"text": text},
            "requestedAttributes": {
                "TOXICITY": {},
                "SEVERE_TOXICITY": {},
                "IDENTITY_ATTACK": {},
                "INSULT": {},
                "PROFANITY": {},
                "THREAT": {},
                "SEXUALLY_EXPLICIT": {},
            },
            "languages": ["es", "en"],
        }

        try:
            response = (
                self._perspective_client.comments()  # type: ignore
                .analyze(body=analyze_request)
                .execute()
            )
        except Exception as e:
            logger.error(f"❌ Error Perspective API: {e}")
            return {
                "service": "perspective",
                "flagged": None,
                "detail": f"Error Perspective: {e}",
            }

        attribute_scores = response.get("attributeScores") or {}
        scores: Dict[str, float] = {}
        flagged_categories: List[str] = []

        for attr, data in attribute_scores.items():
            summary = (data or {}).get("summaryScore") or {}
            score = float(summary.get("value", 0.0))
            scores[str(attr).lower()] = score
            if score >= threshold:
                flagged_categories.append(self._format_category(attr))

        is_flagged = len(flagged_categories) > 0

        return {
            "service": "perspective",
            "flagged": is_flagged,
            "categories": flagged_categories,
            "scores": scores,
            "detail": (
                f"Perspective detectó: {', '.join(flagged_categories)}"
                if is_flagged
                else "Aprobado por Perspective"
            ),
        }

    # -----------------------------
    # Combinadores
    # -----------------------------
    def _evaluate_with_consensus(
        self, openai_result: Dict[str, Any], perspective_result: Dict[str, Any]
    ) -> ContentModerationResult:
        o_flag = openai_result.get("flagged")
        p_flag = perspective_result.get("flagged")

        if o_flag is None and p_flag is not None:
            return self._single_service_result(perspective_result, "perspective")
        if p_flag is None and o_flag is not None:
            return self._single_service_result(openai_result, "openai")
        if o_flag is None and p_flag is None:
            return ContentModerationResult(
                allowed=True,
                flagged=False,
                detail="No se pudo verificar (servicios no disponibles)",
                confidence="none",
            )

        if o_flag and p_flag:
            cats = list(
                set(
                    openai_result.get("categories", [])
                    + perspective_result.get("categories", [])
                )
            )
            return ContentModerationResult(
                allowed=False,
                flagged=True,
                detail="Rechazado por ambos servicios",
                categories=cats,
                confidence="very_high",
            )
        if not o_flag and not p_flag:
            return ContentModerationResult(
                allowed=True,
                flagged=False,
                detail="Aprobado por ambos servicios",
                confidence="high",
            )

        service = "openai" if o_flag else "perspective"
        result = openai_result if o_flag else perspective_result
        return ContentModerationResult(
            allowed=False,
            flagged=True,
            detail=f"Rechazado por {service} (sin consenso)",
            categories=result.get("categories", []),
            confidence="medium",
        )

    def _evaluate_any_reject(
        self, openai_result: Dict[str, Any], perspective_result: Dict[str, Any]
    ) -> ContentModerationResult:
        o_flag = bool(openai_result.get("flagged", False))
        p_flag = bool(perspective_result.get("flagged", False))

        if o_flag or p_flag:
            # Si ambos rechazan, combinamos categorías
            if o_flag and p_flag:
                cats = list(
                    set(
                        openai_result.get("categories", [])
                        + perspective_result.get("categories", [])
                    )
                )
                return ContentModerationResult(
                    allowed=False,
                    flagged=True,
                    detail="Rechazado (OpenAI & Perspective)",
                    categories=cats,
                    confidence="high",
                )

            result = openai_result if o_flag else perspective_result
            return ContentModerationResult(
                allowed=False,
                flagged=True,
                detail=result.get("detail", "Contenido rechazado"),
                categories=result.get("categories", []),
                confidence="medium",
            )

        # Si ninguno rechazó, aprobar
        confidence = "medium" if perspective_result.get("flagged") is None else "high"
        return ContentModerationResult(
            allowed=True,
            flagged=False,
            detail="Contenido aprobado",
            confidence=confidence,
        )

    def _single_service_result(
        self, result: Dict[str, Any], service: str
    ) -> ContentModerationResult:
        if result.get("flagged"):
            return ContentModerationResult(
                allowed=False,
                flagged=True,
                detail=result.get("detail", f"Rechazado por {service}"),
                categories=result.get("categories", []),
                confidence="low",
            )
        return ContentModerationResult(
            allowed=True,
            flagged=False,
            detail=result.get("detail", f"Aprobado por {service}"),
            confidence="low",
        )

    # -----------------------------
    # Filtro local (fallback)
    # -----------------------------
    def _build_local_rules(self) -> List[Tuple[str, re.Pattern]]:
        """Reglas de filtrado local - VERSIÓN ROBUSTA"""
        patterns = [
            # Drogas - Todas las variantes
            (
                "Drogas",
                r"(narco|drug|droga|dealer|traficante|vendedor.*droga|distribuidor.*droga)",
            ),
            # Órganos
            (
                "Tráfico de órganos",
                r"(organ.*dealer|trafico.*organo|venta.*organo)",
            ),
            # Armas
            (
                "Armas",
                r"(sicario|hitman|asesino|killer|arma|weapon|traficante.*arma)",
            ),
            # Sexual
            (
                "Explotación sexual",
                r"(prostitu|proxeneta|pimp|escort.*service|trabajo.*sexual)",
            ),
            # Terrorismo
            (
                "Terrorismo",
                r"(terroris|extremis|yihad|jihad)",
            ),
            # Fraude
            (
                "Fraude",
                r"(fraude|estafa|scam|ponzi|piramidal|phishing)",
            ),
        ]

        compiled: List[Tuple[str, re.Pattern]] = []
        for name, pat in patterns:
            try:
                # CRÍTICO: Sin word boundaries, case insensitive
                compiled.append((name, re.compile(pat, re.IGNORECASE)))
            except Exception:
                pass

        return compiled

    def _check_local(self, text: str) -> ContentModerationResult:
        """Filtro local - VERSIÓN SIMPLE Y EFECTIVA"""
        hits: List[str] = []

        text_lower = text.lower()

        for name, rex in self._local_rules:
            if rex.search(text_lower):
                hits.append(name)

        # Si hay matches, RECHAZAR
        if hits:
            return ContentModerationResult(
                allowed=False,
                flagged=True,
                detail=f"Contenido inapropiado detectado: {', '.join(hits)}",
                categories=hits,
                confidence="high",
            )

        # Si no hay matches, APROBAR
        return ContentModerationResult(
            allowed=True,
            flagged=False,
            detail="Contenido aprobado",
            confidence="high",
        )

    # -----------------------------
    # Utilidades
    # -----------------------------

    @staticmethod
    def _calculate_severity(scores: Dict[str, float]) -> str:
        try:
            values = [
                float(v)
                for v in (scores or {}).values()
                if isinstance(v, (int, float, str))
            ]
            values = [
                v
                for v in [
                    float(x) if not isinstance(x, (int, float)) else x for x in values
                ]
                if 0.0 <= v <= 1.0
            ]
        except Exception:
            values = []
        max_score = max(values) if values else 0.0

        if max_score >= 0.9:
            return "critical"
        if max_score >= 0.7:
            return "high"
        if max_score >= 0.5:
            return "medium"
        if max_score >= 0.3:
            return "low"
        return "minimal"

    @staticmethod
    def _format_category(category: str) -> str:
        return str(category).replace("_", " ").replace("/", " o ").title()


# Singleton
_moderator_instance: Optional[HybridContentModerator] = None


def get_content_moderator() -> HybridContentModerator:
    """Obtiene instancia singleton del moderador (siempre seguro)."""
    global _moderator_instance
    if _moderator_instance is None:
        _moderator_instance = HybridContentModerator(enable_local_fallback=True)
    return _moderator_instance


# ----------------------------------------
# Ejecución directa rápida (smoke test)
#   python content_moderator.py
# ----------------------------------------
if __name__ == "__main__":  # pragma: no cover
    mod = get_content_moderator()
    tests = [
        "Frontend Developer",
        "Buscamos drug dealer para expandir mercado",
        "Organ dealer con experiencia en logística",
        "Senior Backend Engineer (Python, AWS, SQL)",
    ]
    for t in tests:
        res = mod.moderate(t)
        print("TEXT:", t)
        print(res.to_dict())
        print("-" * 60)
