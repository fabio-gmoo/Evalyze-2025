# Guía de Integración - Endpoints de IA con Django Backend

## Descripción General

El servicio de IA ahora proporciona tres flujos principales que deben integrarse en el backend de Django:

1. **Generar Preguntas de Entrevista** → `/generate_interview`
2. **Evaluar Respuestas del Candidato** → `/evaluate_response`
3. **Generar Análisis SWOT** → `/generate_swot_analysis`

---

## Flujo Recomendado de Integración

### Fase 1: Crear Vacante y Entrevista (Actual)
```
1. HR crea vacante con requisitos
2. Backend genera preguntas via /generate_interview
3. Sistema crea InterviewSession con preguntas
```

### Fase 2: Conducir Entrevista (Actual)
```
1. Candidato inicia sesión de entrevista
2. IA realiza preguntas secuencialmente via /chat
3. Sistema guarda respuestas en ChatMessage
```

### Fase 3: Evaluar y Analizar (NUEVO)
```
1. Candidato completa entrevista
2. Sistema itera sobre cada respuesta:
   POST /evaluate_response → Obtener puntuaciones
3. Recopilar todas las evaluaciones
4. POST /generate_swot_analysis → Generar análisis
5. Guardar análisis en base de datos
6. Mostrar en UI
```

---

## Implementación en Django

### Paso 1: Actualizar `InterviewSession` Model

Agregar campos para almacenar evaluaciones:

```python
# jobs/models.py

class InterviewSession(models.Model):
    # ... campos existentes ...
    
    # Nuevos campos para análisis
    evaluations = models.JSONField(
        default=list,
        blank=True,
        help_text="Array de evaluaciones de cada respuesta"
    )
    swot_analysis = models.JSONField(
        null=True,
        blank=True,
        help_text="Análisis SWOT generado"
    )
    final_score = models.FloatField(
        default=0.0,
        help_text="Puntuación final del candidato"
    )
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('HIRE', 'Contratar'),
            ('INTERVIEW_AGAIN', 'Entrevistar nuevamente'),
            ('REJECT', 'Rechazar')
        ],
        null=True,
        blank=True,
        help_text="Recomendación del sistema"
    )
```

### Paso 2: Extender `InterviewService`

Agregar métodos para evaluación y análisis:

```python
# jobs/services/interview_service.py

class InterviewService:
    
    def evaluate_candidate_response(
        self,
        question: Dict,
        response: str
    ) -> Dict:
        """
        Evalúa una respuesta individual del candidato.
        
        Args:
            question: Dict con estructura de pregunta
            response: Texto de respuesta del candidato
            
        Returns:
            Evaluación con puntuaciones
        """
        try:
            with httpx.Client(timeout=120.0) as client:
                api_response = client.post(
                    f"{self.ai_url}/evaluate_response",
                    json={
                        "question": question,
                        "candidate_response": response,
                        "model": "llama3.2"
                    }
                )
                api_response.raise_for_status()
                return api_response.json()
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            raise
    
    def generate_swot_analysis(
        self,
        session: InterviewSession
    ) -> Dict:
        """
        Genera análisis SWOT basado en evaluaciones.
        
        Args:
            session: La sesión de entrevista completada
            
        Returns:
            Análisis SWOT generado
        """
        # Recopilar evaluaciones
        candidate_responses = [
            {
                "question_id": eval_data.get("question_id"),
                "overall_score": eval_data.get("overall_score", 0),
                "feedback": eval_data.get("feedback", ""),
                "strengths": eval_data.get("strengths", []),
                "weaknesses": eval_data.get("weaknesses", [])
            }
            for eval_data in session.evaluations
        ]
        
        config = session.interview_config
        
        try:
            with httpx.Client(timeout=120.0) as client:
                api_response = client.post(
                    f"{self.ai_url}/generate_swot_analysis",
                    json={
                        "vacancy_title": config.get("vacancy_title", ""),
                        "level": config.get("level", "intermedio"),
                        "interview_data": config,
                        "candidate_responses": candidate_responses,
                        "model": "llama3.2"
                    }
                )
                api_response.raise_for_status()
                return api_response.json()
        except Exception as e:
            logger.error(f"Error generating SWOT: {e}")
            raise
    
    def complete_interview_with_analysis(
        self,
        session: InterviewSession
    ) -> Dict:
        """
        Completa la entrevista y genera análisis completo.
        
        Args:
            session: Sesión a completar
            
        Returns:
            Análisis final con recomendación
        """
        logger.info(f"Completing interview {session.id} with analysis")
        
        # Evaluar cada respuesta
        config = session.interview_config
        questions = config.get("questions", [])
        evaluations = []
        
        for i, message in enumerate(session.messages.filter(sender="candidate")):
            if i < len(questions):
                question = questions[i]
                
                try:
                    eval_result = self.evaluate_candidate_response(
                        question,
                        message.content
                    )
                    
                    if eval_result.get("ok"):
                        evaluations.append(eval_result.get("evaluation", {}))
                except Exception as e:
                    logger.warning(f"Failed to evaluate message {i}: {e}")
                    # Guardar al menos estructura vacía
                    evaluations.append({
                        "question_id": question.get("id"),
                        "overall_score": 0,
                        "error": str(e)
                    })
        
        # Guardar evaluaciones
        session.evaluations = evaluations
        session.save()
        
        # Generar SWOT
        try:
            swot_result = self.generate_swot_analysis(session)
            
            if swot_result.get("ok"):
                analysis = swot_result.get("analysis", {})
                
                # Actualizar sesión con análisis
                session.swot_analysis = analysis
                session.final_score = analysis.get("overall_score", 0)
                session.recommendation = analysis.get("recommendation", "INTERVIEW_AGAIN")
                session.complete_session()
                session.save()
                
                logger.info(f"✅ Interview {session.id} completed with analysis")
                return analysis
        except Exception as e:
            logger.warning(f"Failed to generate SWOT: {e}")
            # Aún completar sesión incluso si falla SWOT
            session.complete_session()
            session.save()
        
        return {}
```

### Paso 3: Agregar Endpoint en ViewSet

```python
# jobs/views_interview.py

@action(detail=True, methods=["post"], url_path="complete-and-analyze")
def complete_and_analyze(self, request, pk=None):
    """
    Completa la entrevista y genera análisis SWOT.
    """
    session = self.get_object()
    
    # Verificar permisos
    if session.application.candidate != request.user:
        return Response(
            {"detail": "No tienes permiso"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if session.status != "active":
        return Response(
            {"detail": "Sesión no activa"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = InterviewService()
        analysis = service.complete_interview_with_analysis(session)
        
        return Response({
            "session_id": session.id,
            "status": session.status,
            "analysis": analysis,
            "recommendation": session.recommendation,
            "final_score": session.final_score
        })
    except Exception as e:
        logger.error(f"Error in complete_and_analyze: {e}")
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### Paso 4: Serializer para Análisis

```python
# jobs/serializers.py

class InterviewAnalysisSerializer(serializers.ModelSerializer):
    swot_analysis = serializers.JSONField()
    evaluations = serializers.JSONField()
    
    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'status',
            'final_score',
            'recommendation',
            'evaluations',
            'swot_analysis',
            'completed_at'
        ]
```

---

## Flujo de Uso desde Frontend

### 1. Iniciar Entrevista
```javascript
// Candidato inicia sesión
POST /api/interview-sessions/{id}/start-session

// Respuesta: ai_session_id + first_message
```

### 2. Enviar Respuestas
```javascript
// Para cada pregunta
POST /api/interview-sessions/{id}/send-message
{
  "message": "Mi respuesta es..."
}

// Repetir hasta completar todas
```

### 3. Completar y Analizar
```javascript
// Cuando termina la entrevista
POST /api/interview-sessions/{id}/complete-and-analyze

// Respuesta:
{
  "status": "completed",
  "final_score": 75,
  "recommendation": "HIRE",
  "analysis": {
    "swot": {
      "strengths": [...],
      "weaknesses": [...],
      "opportunities": [...],
      "threats": [...]
    }
  }
}
```

### 4. Mostrar Resultados
```javascript
// En componente de resultados
if (recommendation === "HIRE") {
  // Verde - Contratar
} else if (recommendation === "INTERVIEW_AGAIN") {
  // Amarillo - Entrevistar nuevamente
} else {
  // Rojo - Rechazar
}

// Mostrar SWOT en panels
```

---

## Campos de Respuesta del Análisis SWOT

```json
{
  "ok": true,
  "analysis": {
    "vacancy": "Backend Engineer",
    "level": "intermedio",
    "candidate_level": "intermedio",
    "overall_score": 78,
    "swot": {
      "strengths": [
        {
          "title": "Experiencia técnica",
          "description": "Demostró conocimiento profundo de Node.js",
          "score_reference": 85
        }
      ],
      "weaknesses": [
        {
          "title": "Comunicación",
          "description": "Algunas respuestas fueron poco claras",
          "score_reference": 65
        }
      ],
      "opportunities": [
        "Oportunidad de mejorar skills en PostgreSQL"
      ],
      "threats": [
        "Brecha en arquitectura de sistemas"
      ]
    },
    "recommendation": "HIRE",
    "rationale": "Candidato muestra habilidades técnicas sólidas...",
    "next_steps": [
      "Enviar oferta",
      "Confirmar disponibilidad",
      "Iniciar onboarding"
    ]
  }
}
```

---

## Configuración de Timeouts

Los tiempos de espera recomendados:

- Generar preguntas: **120 segundos**
- Evaluar respuesta: **120 segundos**
- Generar SWOT: **120 segundos**
- Total teórico: **6 minutos** por entrevista

**Recomendación:** Mostrar barra de progreso al usuario durante análisis.

---

## Manejo de Errores

Casos a considerar:

```python
# Si /evaluate_response falla
→ Guardar estructura vacía: {"question_id": "Q1", "overall_score": 0, "error": "..."}
→ Continuar con siguientes respuestas
→ Generar SWOT con datos parciales

# Si /generate_swot_analysis falla
→ Aún completar sesión
→ Guardar evaluaciones individuales
→ Mostrar error al usuario pero permitir seguir

# Si Ollama no disponible
→ HTTPException 502
→ UI muestra: "Servicio de análisis temporalmente indisponible"
```

---

## Testing

```bash
# Ejecutar tests de endpoints
cd ai-service/
python test_endpoints.py

# Verificar integración con Django
python manage.py test jobs.tests.InterviewServiceTest
```

---

## Notas Importantes

1. **Validación:** Todos los datos del análisis SWOT están validados y respaldados por scores numéricos
2. **No inventos:** El sistema NO genera información que no esté en las evaluaciones
3. **Objetividad:** Fortalezas solo si score >= 75, debilidades si score < 70
4. **Escalabilidad:** Diseñado para manejar múltiples evaluaciones en paralelo

---

**Documento creado:** 2025-12-15
**Última actualización:** Cambios implementados en endpoints de IA
