# Guía de Mejora del Servicio de IA - Evalyze

## Cambios Implementados

### 1. **Prompts Optimizados para llama3.2**

Los prompts han sido completamente rediseñados para ser más explícitos y restrictivos:

- **Instrucciones críticas** al inicio del prompt
- **Esquemas JSON exactos** con ejemplos
- **Restricciones obligatorias** claramente marcadas
- **Puntos finales definitivos** que refuerzan el formato esperado

#### Cambios clave:
```
ANTES: "Devuelve ÚNICAMENTE el JSON..."
AHORA: "ACCIÓN FINAL: Devuelve SOLO el JSON. Nada más. Sin comillas de bloque, sin explicaciones, sin comentarios."
```

### 2. **Nuevos Endpoints para Análisis**

Se han agregado dos endpoints críticos:

#### `/evaluate_response` (POST)
- Evalúa una respuesta de candidato a una pregunta
- Retorna puntuaciones objetivas (0-100) para:
  - Relevancia
  - Completitud
  - Palabras clave encontradas
  - Claridad
  - Profundidad
  - Puntuación general

Ejemplo de uso:
```json
{
  "question": {
    "id": "Q1",
    "question": "¿Cuál es tu experiencia con Node.js?",
    "type": "technical",
    "expected_keywords": ["async", "event loop", "npm"],
    "rubric": "Evaluación de experiencia backend",
    "weight": 25
  },
  "candidate_response": "He trabajado con Node.js en proyectos...",
  "model": "llama3.2"
}
```

#### `/generate_swot_analysis` (POST)
- Genera análisis SWOT objetivo basado en evaluaciones
- Solo menciona fortalezas si score >= 75
- Solo menciona debilidades si score < 70
- Todo respaldado con datos numéricos

Ejemplo de uso:
```json
{
  "vacancy_title": "Backend Engineer",
  "level": "intermedio",
  "interview_data": { ... },
  "candidate_responses": [ ... evaluaciones ... ],
  "model": "llama3.2"
}
```

### 3. **Módulo de Validación Mejorado** (`validators.py`)

Nuevo módulo con funciones de validación estricta:

- `validate_interview_questions()` - Valida estructura de preguntas
- `validate_response_evaluation()` - Valida evaluaciones de respuestas
- `validate_swot_analysis()` - Valida análisis SWOT
- `extract_json_from_text()` - Extrae JSON robustamente de respuestas
- `sanitize_json_score()` - Asegura que scores sean válidos 0-100

### 4. **Mejor Manejo de Reintentos**

Cada endpoint ahora implementa:
- Hasta 2 reintentos automáticos
- Prompts de corrección específicos
- Validación estructurada antes de retornar
- Logs detallados para debugging

### 5. **Prompt del Sistema de Entrevista Mejorado**

El sistema prompt para el entrevistador ahora:
- Es más restrictivo en preguntas de seguimiento
- Mantiene un flujo lineal (pregunta 1 → 2 → 3...)
- Da respuestas más cortas y naturales
- Tiene instrucciones claras para cierre

## Cómo Funciona el Flujo Mejorado

### Generación de Preguntas de Entrevista

```
1. Client POST /generate_interview
   ↓
2. AI genera JSON de preguntas
   ↓
3. Validación estricta (estructura, tipos, pesos)
   ↓
4. Si falla → Reintento automático con prompt de corrección
   ↓
5. Return JSON validado
```

### Evaluación de Respuesta

```
1. Client POST /evaluate_response
   ↓
2. AI evalúa respuesta con 5 criterios
   ↓
3. Genera scores 0-100 para cada criterio
   ↓
4. Calcula overall_score
   ↓
5. Validación de estructura
   ↓
6. Return evaluación con scores
```

### Análisis SWOT

```
1. Client POST /generate_swot_analysis
   ↓
2. AI recibe evaluaciones numéricas
   ↓
3. Genera SWOT basado SOLO en datos:
   - Fortalezas si score >= 75
   - Debilidades si score < 70
   ↓
4. Validación de estructura y datos
   ↓
5. Return análisis con recomendación
```

## Configuración Recomendada

### Variables de Entorno

```bash
# .env o docker-compose.yml
OLLAMA_URL=http://ollama:11434/api/generate
OLLAMA_MODEL=llama3.2  # Debe ser llama3.2 o compatible
```

### Parámetros de Ollama

```python
# ollama_client.py - Parámetros optimizados para llama3.2
{
    "temperature": 0.2,      # Bajo para determinismo
    "top_k": 40,             # Limita vocabulario
    "top_p": 0.9,            # Núcleo de sampleo
    "num_predict": 1024      # Máximo de tokens
}
```

## Testeo de los Cambios

### 1. Generar preguntas de entrevista

```bash
curl -X POST http://localhost:8001/generate_interview \
  -H "Content-Type: application/json" \
  -d '{
    "vacancy_title": "Backend Engineer",
    "requirements": ["Node.js", "PostgreSQL", "REST APIs"],
    "level": "intermedio",
    "n_questions": 4,
    "model": "llama3.2"
  }'
```

Verificar:
- ✅ JSON válido retornado
- ✅ Exactamente 4 preguntas
- ✅ Total de weight = 100
- ✅ Cada pregunta tiene campos requeridos

### 2. Evaluar respuesta

```bash
curl -X POST http://localhost:8001/evaluate_response \
  -H "Content-Type: application/json" \
  -d '{
    "question": {
      "id": "Q1",
      "question": "¿Cuál es tu experiencia con Node.js?",
      "type": "technical",
      "expected_keywords": ["async", "event loop", "npm"],
      "rubric": "Evaluación técnica",
      "weight": 25
    },
    "candidate_response": "Tengo 3 años de experiencia con Node.js...",
    "model": "llama3.2"
  }'
```

Verificar:
- ✅ Todos los scores son 0-100
- ✅ overall_score ≈ promedio de otros scores
- ✅ Arrays tienen strings (no vacío)
- ✅ Feedback es coherente con scores

### 3. Generar análisis SWOT

```bash
curl -X POST http://localhost:8001/generate_swot_analysis \
  -H "Content-Type: application/json" \
  -d '{
    "vacancy_title": "Backend Engineer",
    "level": "intermedio",
    "interview_data": { ... },
    "candidate_responses": [ ... ],
    "model": "llama3.2"
  }'
```

Verificar:
- ✅ SWOT tiene 4 secciones
- ✅ Fortalezas solo si scores >= 75
- ✅ Debilidades solo si scores < 70
- ✅ Recomendación es HIRE, INTERVIEW_AGAIN o REJECT
- ✅ NO hay datos inventados (solo basado en evaluaciones)

## Cambios en Frontend/Backend de Django

### En `jobs/services/interview_service.py`

El prompt del sistema ahora es más restrictivo:
- Sin preguntas de seguimiento
- Flujo lineal de preguntas
- Cierre automático

### Integración futura recomendada

Para integrar completamente, en Django backend:

```python
# Después de que candidato complete entrevista:

1. Obtener todas las respuestas del candidato
2. Para cada respuesta: POST /evaluate_response
3. Recopilar todas las evaluaciones
4. POST /generate_swot_analysis con evaluaciones
5. Guardar análisis en base de datos
6. Mostrar en UI
```

## Troubleshooting

### Problema: JSON malformado en respuestas

**Causa:** llama3.2 añade comillas o markdown alrededor del JSON

**Solución:** El extractor `extract_json_from_text()` ya maneja esto automáticamente

### Problema: Scores incoherentes

**Causa:** overall_score no coincide con promedio

**Solución:** Implementado `sanitize_json_score()` que corrige automáticamente

### Problema: SWOT con datos inventados

**Causa:** Prompt insuficientemente restrictivo

**Solución:** Nuevo prompt con restricciones explícitas y validación de datos

### Problema: Fallo después de reintentos

**Solución:** Revisar logs en:
```bash
docker logs evalyze-ai-service
```

## Performance y Recursos

- **Temperatura:** 0.2 (bajo = más determinista, mejor para JSON)
- **Tokens máximos:** 1024 por respuesta
- **Timeouts:** 120 segundos por llamada a Ollama
- **Reintentos:** Máximo 2 intentos automáticos

## Próximos Pasos

1. **Enriquecer Knowledge Base** - Agregar más ejemplos en `kb/`
2. **Calibración de pesos** - Ajustar weights según importancia real
3. **Métricas** - Implementar tracking de accuracy de evaluaciones
4. **Feedback loop** - Usar ACTUAL evaluaciones de HR para mejorar prompts
