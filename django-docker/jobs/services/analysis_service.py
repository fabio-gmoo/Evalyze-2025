# django-docker/jobs/services/analysis_service.py


import httpx  # type: ignore

import logging

import os

import re

import json

from typing import Dict, List, Any

from django.utils import timezone  # type: ignore

from collections import Counter

from jobs.models import InterviewSession


logger = logging.getLogger(__name__)


AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8001")


class InterviewAnalysisService:
    """Service to analyze interview sessions using SWOT methodology"""

    def __init__(self):
        self.ai_url = AI_SERVICE_URL

    def analyze_interview(self, session: InterviewSession) -> Dict[str, Any]:
        """
        Analyze a completed interview session using SWOT methodology
        """
        if session.status != "completed":
            # Opcional: permitir análisis incluso si no está marcado como "completed" en DB
            # para pruebas, o mantener la restricción:
            # raise ValueError("Session must be completed before analysis")
            pass

        # 1. Gather interview data
        interview_data = self._prepare_interview_data(session)

        # --- AQUÍ ESTABA EL FALTANTE ---
        # 2. Generar Puntuación Técnica con IA (Esto es lo que arregla el 20%)
        scoring_result = self._generate_ai_scoring(interview_data)

        # Actualizar el score de la sesión con el resultado de la IA
        new_total_score = scoring_result.get("total_score", 0)
        session.total_score = new_total_score

        # Actualizamos interview_data con el nuevo score para que el FODA lo tenga en cuenta
        interview_data["total_score"] = new_total_score
        interview_data["scoring_details"] = scoring_result.get("details", [])
        # -------------------------------

        # 3. Generate SWOT analysis using AI
        swot_analysis = self._generate_swot_analysis(interview_data)

        # 4. Calculate quantitative score
        quantitative_score = self._calculate_score(session, swot_analysis)

        # 5. Generate cross-SWOT strategies
        cross_swot = self._generate_cross_swot(swot_analysis)

        # 6. Generate recommendations
        recommendations = self._generate_recommendations(
            swot_analysis, quantitative_score
        )

        # Build final report
        report = {
            "candidate_id": session.application.candidate.id,
            "candidate_name": session.application.candidate.name,
            "candidate_email": session.application.candidate.email,
            "vacancy_id": session.application.vacancy.id,
            "vacancy_title": session.application.vacancy.puesto,
            "company_name": session.company_name,
            "interview_date": session.completed_at.isoformat()
            if session.completed_at
            else None,
            "quantitative_score": quantitative_score,
            "score_category": self._get_score_category(quantitative_score),
            # Agregamos el desglose para poder verlo en el front si quieres
            "technical_score_breakdown": scoring_result.get("details", []),
            "swot_analysis": swot_analysis,
            "cross_swot": cross_swot,
            "recommendations": recommendations,
            "metadata": {
                "total_questions": len(session.interview_config.get("questions", [])),
                "total_messages": session.messages.count(),
                "duration_minutes": self._calculate_duration(session),
            },
        }

        # Save report to session
        session.analysis_report = report
        # Importante: guardar también el total_score actualizado
        session.save(update_fields=["analysis_report", "total_score"])

        return report

    def _prepare_interview_data(self, session: InterviewSession) -> Dict[str, Any]:
        """Prepare interview data for AI analysis"""

        messages = session.messages.all().order_by("timestamp")

        conversation = []

        for msg in messages:
            # Incluimos solo mensajes relevantes para el análisis (no saludos vacíos del sistema)

            conversation.append(
                {
                    "sender": msg.sender,
                    "content": msg.content,
                    "question_index": msg.question_index,
                }
            )

        questions = session.interview_config.get("questions", [])

        return {
            "vacancy_title": session.application.vacancy.puesto,
            "vacancy_requirements": session.application.vacancy.requisitos.split("\n")
            if session.application.vacancy.requisitos
            else [],
            "questions": questions,
            "conversation": conversation,
            # Enviamos el max score actual (o 100 por defecto para normalizar)
            "max_possible_score": session.max_possible_score or 100.0,
        }

    def _generate_ai_scoring(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """

        NUEVO: Evalúa técnicamente las respuestas y asigna un puntaje.

        """

        prompt = self._build_scoring_prompt(data)

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.ai_url}/chat/start",
                    json={
                        "system": "Eres un evaluador técnico experto. Tu trabajo es calificar objetivamente entrevistas.",
                        "model": "llama3.2",
                    },
                )

                response.raise_for_status()

                session_id = response.json().get("session_id")

                analysis_response = client.post(
                    f"{self.ai_url}/chat/message",
                    json={
                        "session_id": session_id,
                        "text": prompt,
                        "model": "llama3.2",
                    },
                )

                analysis_response.raise_for_status()

                result_text = analysis_response.json().get("message", "")

                return self._parse_json_response(
                    result_text, default={"total_score": 50, "details": []}
                )

        except Exception as e:
            logger.error(f"Error generating AI scoring: {e}", exc_info=True)

            return {"total_score": 0, "details": []}

    def _build_scoring_prompt(self, data: Dict[str, Any]) -> str:
        conversation_text = "\n".join(
            [
                f"{msg['sender'].upper()}: {msg['content']}"
                for msg in data["conversation"]
            ]
        )

        requirements_text = "\n".join(
            [f"- {req}" for req in data["vacancy_requirements"]]
        )

        return f"""Actúa como un Evaluador Técnico Senior.

Analiza la siguiente entrevista para la vacante: {data["vacancy_title"]}


REQUISITOS DEL PUESTO:

{requirements_text}


TRANSCRIPCIÓN:

{conversation_text}


TAREA:

1. Evalúa qué tan bien cumple el candidato con los requisitos basándote EXCLUSIVAMENTE en sus respuestas.

2. Asigna un puntaje global del 0 al 100.

3. Provee un desglose breve.


Responde ÚNICAMENTE con este formato JSON:

{{

    "total_score": (número entero 0-100),

    "details": [

        {{ "aspect": "Conocimiento Técnico", "score": (

            0-10), "comment": "breve explicación" }},

        {{ "aspect": "Experiencia", "score": (

            0-10), "comment": "breve explicación" }},

        {{ "aspect": "Comunicación", "score": (

            0-10), "comment": "breve explicación" }}

    ]

}}

"""

    def _generate_swot_analysis(
        self, interview_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate SWOT analysis using AI"""

        prompt = self._build_swot_prompt(interview_data)

        try:
            with httpx.Client(timeout=120.0) as client:
                # Usamos una sesión nueva para evitar contaminación de contexto

                response = client.post(
                    f"{self.ai_url}/chat/start",
                    json={
                        "system": "Eres un experto analista de RRHH. Tu idioma es ESPAÑOL.",
                        "model": "llama3.2",
                    },
                )

                response.raise_for_status()

                session_id = response.json().get("session_id")

                analysis_response = client.post(
                    f"{self.ai_url}/chat/message",
                    json={
                        "session_id": session_id,
                        "text": prompt,
                        "model": "llama3.2",
                    },
                )

                analysis_response.raise_for_status()

                return self._parse_swot_response(
                    analysis_response.json().get("message", "")
                )

        except Exception as e:
            logger.error(f"Error generating SWOT: {e}", exc_info=True)

            return self._generate_fallback_swot(interview_data)

    def _build_swot_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for SWOT analysis in Spanish"""

        conversation_text = "\n".join(
            [
                f"{msg['sender'].upper()}: {msg['content']}"
                for msg in data["conversation"]
            ]
        )

        requirements_text = "\n".join(
            [f"- {req}" for req in data["vacancy_requirements"]]
        )

        # Mantenemos las claves del JSON en inglés (strengths, weaknesses...) para que el código Python

        # siga funcionando sin cambios, pero pedimos que el CONTENIDO (los valores) sea en ESPAÑOL.

        return f"""Analiza esta entrevista de trabajo utilizando la metodología FODA (SWOT).


VACANTE: {data["vacancy_title"]}


REQUISITOS:

{requirements_text}


CONVERSACIÓN DE LA ENTREVISTA:

{conversation_text}


PUNTAJE DE ENTREVISTA: {data["total_score"]}/{data["max_possible_score"]}


Por favor proporciona un análisis FODA completo en el siguiente formato JSON estricto.

IMPORTANTE: El contenido del texto dentro de las listas debe estar en ESPAÑOL. Ademas tiene que tener un analisis profesional que pueda identificar verdaderamente las cualidades requeridas para un analisis FODA.


{{

  "strengths": ["lista de 4-6 fortalezas específicas demostradas (en español)"],

  "weaknesses": ["lista de 4-6 debilidades o brechas específicas (en español)"],

  "opportunities": ["lista de 4-6 oportunidades de crecimiento (en español)"],

  "threats": ["lista de 4-6 riesgos potenciales (en español)"]

}}


Cada punto debe ser:

- Específico para la entrevista de este candidato

- Accionable y medible donde sea posible

- Directamente relacionado con los requisitos de la vacante

- Respaldado por evidencia de la conversación


Responde SOLAMENTE con la estructura JSON, sin texto adicional."""

    def _parse_json_response(self, response: str, default: Any) -> Any:
        """Helper robusto para limpiar y parsear JSON de la IA"""

        try:
            # Intenta encontrar bloques de código json

            pattern = r"```(?:json)?\s*(.*?)\s*```"

            match = re.search(pattern, response, re.DOTALL)

            clean_text = match.group(1) if match else response.strip()

            # Buscar llaves para extraer solo el objeto

            start = clean_text.find("{")

            end = clean_text.rfind("}") + 1

            if start >= 0 and end > start:
                return json.loads(clean_text[start:end])

            return default

        except Exception as e:
            logger.warning(f"Error parsing AI JSON: {e}")

            return default

    def _parse_swot_response(self, response: str) -> Dict[str, List[str]]:
        # Usamos el helper genérico pero aseguramos las llaves

        data = self._parse_json_response(response, default={})

        required_keys = ["strengths", "weaknesses", "opportunities", "threats"]

        # Normalizar claves a minúsculas

        normalized = {k.lower(): v for k, v in data.items()}

        if all(key in normalized for key in required_keys):
            return normalized

        return self._generate_fallback_swot(
            {"total_score": 0, "max_possible_score": 100, "questions": []}
        )

    def _generate_fallback_swot(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Fallback simple en español"""

        return {
            "strengths": [
                "El candidato completó la entrevista",
                "Mostró interés en la posición",
            ],
            "weaknesses": ["No se pudo generar un análisis profundo detallado"],
            "opportunities": ["Realizar una segunda entrevista técnica"],
            "threats": ["Evaluación automática inconclusa"],
        }

    def _calculate_score(
        self, session: InterviewSession, swot: Dict[str, List[str]]
    ) -> float:
        """

        Calculate quantitative score as percentage.

        Ahora usa el total_score real calculado por la IA.

        """

        # 1. Base score (Evaluación técnica de la IA 0-100)

        # Ya viene en escala 0-100 desde _generate_ai_scoring

        ai_technical_score = session.total_score

        # Ponderación: 70% Conocimiento Técnico (IA Score) + 30% Balance FODA

        weighted_tech_score = ai_technical_score * 0.70

        # 2. SWOT balance score (30%)

        strength_count = len(swot.get("strengths", []))

        weakness_count = len(swot.get("weaknesses", []))

        if strength_count + weakness_count > 0:
            balance_ratio = strength_count / (strength_count + weakness_count)

            # Si tiene más fortalezas que debilidades, sube el score

            swot_score = balance_ratio * 30

        else:
            swot_score = 15  # Neutral

        total_score = weighted_tech_score + swot_score

        return round(min(total_score, 100.0), 2)

    # ... (El resto de métodos de reportes agregados get_vacancy_ranking, etc. se mantienen igual)

    # Solo asegúrate de copiar los métodos auxiliares que no modifiqué si los usas.

    def _generate_cross_swot(self, swot: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Generate Cross-SWOT strategies (Translated to Spanish)"""

        strengths = swot.get("strengths", [])

        weaknesses = swot.get("weaknesses", [])

        opportunities = swot.get("opportunities", [])

        threats = swot.get("threats", [])

        # Helpers for safe slicing strings

        def safe_slice(lst, idx):
            val = lst[idx] if idx < len(lst) else "este factor"

            return val[:50] + "..." if len(val) > 50 else val

        return {
            "so_strategies": [
                f"Aprovechar {safe_slice(strengths, i)} para capitalizar {
                    safe_slice(opportunities, i)
                }"
                for i in range(min(3, len(strengths), len(opportunities)))
            ]
            if strengths and opportunities
            else ["Basarse en fortalezas para perseguir oportunidades"],
            "wo_strategies": [
                f"Abordar {safe_slice(weaknesses, i)} para tomar ventaja de {
                    safe_slice(opportunities, i)
                }"
                for i in range(min(3, len(weaknesses), len(opportunities)))
            ]
            if weaknesses and opportunities
            else ["Mejorar debilidades para desbloquear oportunidades"],
            "st_strategies": [
                f"Usar {safe_slice(strengths, i)} para mitigar {safe_slice(threats, i)}"
                for i in range(min(3, len(strengths), len(threats)))
            ]
            if strengths and threats
            else ["Aplicar fortalezas para minimizar amenazas"],
            "wt_strategies": [
                f"Minimizar {safe_slice(weaknesses, i)} para evitar {
                    safe_slice(threats, i)
                }"
                for i in range(min(3, len(weaknesses), len(threats)))
            ]
            if weaknesses and threats
            else ["Reducir debilidades para prevenir amenazas"],
        }

    def _generate_recommendations(
        self, swot: Dict[str, List[str]], score: float
    ) -> List[str]:
        """Generate actionable recommendations (Translated to Spanish)"""

        recommendations = []

        # Score-based recommendations

        if score >= 80:
            recommendations.append(
                "ALTAMENTE RECOMENDADO: El candidato demuestra un excelente ajuste para la posición"
            )

        elif score >= 60:
            recommendations.append(
                "RECOMENDADO: El candidato muestra buen potencial con áreas menores de desarrollo"
            )

        elif score >= 40:
            recommendations.append(
                "CONDICIONAL: Considerar para la posición con un plan de capacitación específico"
            )

        else:
            recommendations.append(
                "NO RECOMENDADO: Brechas significativas en los requisitos"
            )

        # SWOT-based recommendations

        strengths = swot.get("strengths", [])

        weaknesses = swot.get("weaknesses", [])

        if strengths:
            recommendations.append(
                f"Enfocarse en la fortaleza clave del candidato: {strengths[0][:100]}"
            )

        if weaknesses:
            recommendations.append(
                f"Área de desarrollo a abordar: {weaknesses[0][:100]}"
            )

        recommendations.append("Programar evaluación técnica de seguimiento")

        recommendations.append("Solicitar portafolio o muestras de trabajo")

        recommendations.append("Verificar referencias y experiencia previa")

        return recommendations

    def _get_score_category(self, score: float) -> str:
        """Get category label for score (Translated)"""

        if score >= 80:
            return "Excelente"

        elif score >= 60:
            return "Bueno"

        elif score >= 40:
            return "Regular"

        else:
            return "Pobre"

    def _calculate_duration(self, session: InterviewSession) -> int:
        """Calculate interview duration in minutes"""

        if session.started_at and session.completed_at:
            delta = session.completed_at - session.started_at

            return int(delta.total_seconds() / 60)

        return 0

    def get_vacancy_ranking(
        self, vacancy_id: int, top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """Obtiene los 20 mejores candidatos ordenados por puntaje"""

        from jobs.models import InterviewSession

        # Buscamos sesiones completadas

        sessions = InterviewSession.objects.filter(
            application__vacancy_id=vacancy_id, status="completed"
        ).select_related("application", "application__candidate")

        ranking_data = []

        for session in sessions:
            # Usamos el puntaje final calculado (que puede incluir balance SWOT)

            score = session.get_score_percentage()

            ranking_data.append(
                {
                    "candidate_id": session.application.candidate.id,
                    "candidate_name": session.application.candidate.name,
                    "candidate_email": session.application.candidate.email,
                    "score": score,
                    "category": self._get_score_category(score),
                    "completed_at": session.completed_at,
                    "session_id": session.id,
                }
            )

        # Ordenamos por puntaje descendente en Python para asegurar consistencia

        ranking_data.sort(key=lambda x: x["score"], reverse=True)

        # Devolvemos solo los top N

        return ranking_data[:top_n]

    def generate_vacancy_report(self, vacancy_id: int) -> Dict[str, Any]:
        """Genera un reporte consolidado solo para una vacante específica"""

        # Importación local para evitar ciclos

        from jobs.models import InterviewSession, Vacante

        # Validar existencia

        try:
            vacancy = Vacante.objects.get(id=vacancy_id)

        except Vacante.DoesNotExist:
            return {"error": "Vacante no encontrada"}

        # Filtrar solo sesiones de esta vacante

        sessions = InterviewSession.objects.filter(
            application__vacancy_id=vacancy_id,
            status="completed",
            analysis_report__isnull=False,
        )

        # Reutilizamos la lógica de agregación (extraeremos esto a un método común si es necesario,

        # o copiamos la lógica de generate_global_report pero usando 'sessions' filtradas)

        return self._generate_aggregated_report(
            sessions, title=f"Ranking: {vacancy.puesto}"
        )

    def _generate_aggregated_report(self, sessions, title="") -> Dict[str, Any]:
        """Método auxiliar para calcular estadísticas de un grupo de sesiones"""

        if not sessions.exists():
            return {
                "message": "No hay suficientes datos para generar el ranking.",
                "total_interviews": 0,
                "empty": True,
            }

        total_interviews = sessions.count()

        # Calcular promedios usando el método del modelo get_score_percentage() si es posible,

        # o accediendo al reporte JSON guardado

        scores = []

        for s in sessions:
            if s.analysis_report and "quantitative_score" in s.analysis_report:
                scores.append(float(s.analysis_report["quantitative_score"]))

            else:
                scores.append(0)

        avg_score = sum(scores) / len(scores) if scores else 0

        # Distribución

        dist = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}

        for s in scores:
            if s >= 80:
                dist["excellent"] += 1

            elif s >= 60:
                dist["good"] += 1

            elif s >= 40:
                dist["fair"] += 1

            else:
                dist["poor"] += 1

        # Extraer temas comunes (Fortalezas/Debilidades)

        all_strengths = []

        all_weaknesses = []

        for s in sessions:
            if s.analysis_report:
                swot = s.analysis_report.get("swot_analysis", {})

                all_strengths.extend(swot.get("strengths", []))

                all_weaknesses.extend(swot.get("weaknesses", []))

        return {
            "title": title,
            "report_date": timezone.now().isoformat(),
            "summary": {
                "total_interviews": total_interviews,
                "average_score": round(avg_score, 2),
                "score_distribution": dist,
            },
            "insights": {
                "top_strengths": self._extract_themes(all_strengths)[:5],
                "common_weaknesses": self._extract_themes(all_weaknesses)[:5],
            },
            "empty": False,
        }

    def _extract_themes(self, items: List[str]) -> List[str]:
        """Extract common themes from list of items"""

        # Simple keyword extraction (in production, use NLP)

        keywords = []

        stop_words = {
            "para",
            "como",
            "esta",
            "pero",
            "sobre",
            "entre",
            "tiene",
            "falta",
            "poco",
            "buen",
            "buena",
            "el",
            "la",
            "los",
            "las",
            "un",
            "una",
            "que",
            "del",
            "con",
            "por",
        }

        for item in items:
            # Basic cleanup

            clean_item = re.sub(r"[^\w\s]", "", item.lower())

            words = clean_item.split()

            keywords.extend([w for w in words if len(w) > 4 and w not in stop_words])

        common = Counter(keywords).most_common(10)

        return [word for word, count in common if count > 1]

    def _calculate_interview_quality(self, sessions) -> float:
        """Calculate overall interview quality score"""

        session_list = list(sessions)

        if not session_list:
            return 0.0

        # Count average questions

        total_questions = 0

        for session in session_list:
            questions = session.interview_config.get("questions", [])

            total_questions += len(questions) if isinstance(questions, list) else 0

        avg_questions = total_questions / len(session_list) if session_list else 0

        avg_duration = sum(self._calculate_duration(s) for s in session_list) / len(
            session_list
        )

        # Quality based on completeness and depth

        quality = (min(avg_questions / 5, 1) * 50) + (min(avg_duration / 30, 1) * 50)

        return round(quality, 2)

    def _calculate_requirement_fulfillment(self, sessions) -> float:
        """Calculate how well candidates meet requirements"""

        session_list = list(sessions)

        if not session_list:
            return 0.0

        total_score = sum(
            session.analysis_report.get("quantitative_score", 0)
            for session in session_list
            if session.analysis_report
        )

        return round(total_score / len(session_list), 2)

    def _calculate_engagement_score(self, sessions) -> float:
        """Calculate candidate engagement score"""

        session_list = list(sessions)

        if not session_list:
            return 0.0

        completed = sum(1 for s in session_list if s.status == "completed")

        total = len(session_list)

        return round((completed / total) * 100, 2) if total > 0 else 0.0
