# 🚀 GUÍA DE DESPLIEGUE - Mejoras del Servicio de IA

## Archivos Modificados/Creados

### Código Python
```
ai-service/
├── main.py                    ✏️  MODIFICADO (130 líneas nuevas)
├── validators.py              🆕 NUEVO (200+ líneas)
├── ollama_client.py           ✏️  MODIFICADO (parámetros)
├── test_endpoints.py          🆕 NUEVO (400+ líneas)
└── AI_IMPROVEMENTS.md         ✏️  ACTUALIZADO

django-docker/
└── jobs/services/
    └── interview_service.py   ✏️  MODIFICADO (prompt del sistema)
```

### Documentación
```
Evalyze-2025/
├── README_MEJORAS_IA.md       🆕 NUEVO (Resumen ejecutivo)
├── CAMBIOS_IA_RESUMEN.md      🆕 NUEVO (Resumen detallado)
├── GUIA_INTEGRACION_DJANGO.md 🆕 NUEVO (Integración)
└── VALIDACION_CHECKLIST.md    🆕 NUEVO (Checklist)
```

## Pasos de Despliegue

### 1️⃣ Preparación

```bash
# Clonar o sincronizar cambios
cd Evalyze-2025/

# Verificar archivos
ls ai-service/main.py
ls ai-service/validators.py
ls django-docker/jobs/services/interview_service.py
```

### 2️⃣ Validación de Sintaxis

```bash
cd ai-service/

# Python 3.10+
python -m py_compile main.py validators.py ollama_client.py

# Debe completar sin errores
echo "✅ Sintaxis validada"
```

### 3️⃣ Rebuildar Imagen Docker (AI Service)

```bash
# Opción A: Desde compose
docker-compose down evalyze-ai-service
docker-compose up --build evalyze-ai-service

# Opción B: Manually
cd ai-service/
docker build -t evalyze-ai-service:latest .
docker run -d \
  --name evalyze-ai-service \
  -p 8001:8001 \
  --network evalyze-network \
  evalyze-ai-service:latest
```

### 4️⃣ Verificar Servicios

```bash
# Verificar Ollama
curl http://localhost:11434/api/tags
# Debe retornar: {"models": [...]}

# Verificar AI Service
curl http://localhost:8001/healthz
# Debe retornar: {"status": "ok"}

# Verificar Django
curl http://localhost:8000/api/
# Debe retornar: JSON válido
```

### 5️⃣ Ejecutar Tests

```bash
cd ai-service/

# Test completo (toma 5-10 minutos)
python test_endpoints.py

# Debe mostrar:
# ✅ TEST 1: Health Check Endpoints
# ✅ TEST 2: Generate Interview Questions  
# ✅ TEST 3: Evaluate Candidate Response
# ✅ TEST 4: Generate SWOT Analysis
# ✅ TEST SUITE COMPLETED
```

### 6️⃣ Integración con Django (Opcional)

```bash
# Si quieres usar los nuevos endpoints en Django
cd django-docker/

# Actualizar models.py (agregar campos)
# Actualizar services/interview_service.py (agregar métodos)
# Ver GUIA_INTEGRACION_DJANGO.md

python manage.py migrate
```

## Verificación Post-Despliegue

### ✅ Checklist

- [ ] Ollama está corriendo y accesible
- [ ] AI service inició sin errores
- [ ] Tests completaron exitosamente
- [ ] No hay errores en logs: `docker logs evalyze-ai-service`
- [ ] Endpoints `/evaluate_response` y `/generate_swot_analysis` responden
- [ ] Generador de preguntas sigue funcionando
- [ ] Modelo llama3.2 está disponible

### 📊 Monitoreo

```bash
# Ver logs en tiempo real
docker logs -f evalyze-ai-service

# Buscar errores
docker logs evalyze-ai-service | grep ERROR

# Revisar últimas N líneas
docker logs --tail 50 evalyze-ai-service
```

## Rollback (Si es necesario)

```bash
# Revertir a versión anterior
git checkout HEAD~1 ai-service/main.py
git checkout HEAD~1 ai-service/validators.py
git checkout HEAD~1 django-docker/jobs/services/interview_service.py

# Rebuildar
docker-compose down evalyze-ai-service
docker-compose up --build evalyze-ai-service
```

## Configuración de Producción

### Environment Variables

```bash
# .env
OLLAMA_URL=http://ollama:11434/api/generate
OLLAMA_MODEL=llama3.2
AI_SERVICE_TIMEOUT=120  # segundos
MAX_RETRIES=2           # reintentos automáticos
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

### Docker Compose Update

```yaml
# docker-compose.yml
services:
  ai-service:
    build: ./ai-service
    ports:
      - "8001:8001"
    environment:
      - OLLAMA_URL=http://ollama:11434/api/generate
      - LOG_LEVEL=INFO
    depends_on:
      - ollama
    restart: always
    
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: always

volumes:
  ollama_data:
```

## Performance y Escalabilidad

### Timeouts Recomendados

```
- Generar preguntas: 120 segundos
- Evaluar respuesta: 120 segundos  
- Generar SWOT: 120 segundos
- Total por entrevista: ~360 segundos (6 minutos)
```

### Recursos Necesarios

```
CPU: 2+ cores
RAM: 4+ GB (recomendado 8GB)
GPU: Opcional pero recomendado para llama3.2
Disco: 20+ GB (para modelo Ollama)
```

### Limites de Concurrencia

```python
# Ollama es single-threaded por defecto
# Para múltiples solicitudes simultáneas:
# 1. Usar thread pool en Python
# 2. O escalar Ollama (ejecutar múltiples instancias)
# 3. Implementar cola de tareas (Celery)
```

## Troubleshooting

### ❌ Error: "Cannot connect to Ollama"

```bash
# Verificar conexión
curl http://ollama:11434/api/tags

# Si falla, iniciar Ollama
docker run -d -p 11434:11434 ollama/ollama:latest

# Cargar modelo
docker exec <container_id> ollama pull llama3.2
```

### ❌ Error: "Model not found"

```bash
# Verificar modelos disponibles
curl http://ollama:11434/api/tags

# Instalar modelo
docker exec <ollama_container> ollama pull llama3.2
```

### ❌ Error: "JSON parsing failed"

```bash
# Aumentar verbosidad de logs
export LOG_LEVEL=DEBUG

# Ejecutar tests con verbose
python test_endpoints.py -v

# Revisar respuesta bruta
curl -v http://localhost:8001/generate_interview
```

### ❌ Error: "Timeout exceeded"

```bash
# Revisar logs
docker logs evalyze-ai-service | grep timeout

# Aumentar timeout en ollama_client.py
# timeout=120 → timeout=180

# Revisar recursos del sistema
docker stats ollama
```

## Maintenance

### Limpieza de Caché

```bash
cd ai-service/
rm -rf __pycache__/
find . -name "*.pyc" -delete
```

### Actualizar Dependencias

```bash
pip install -r requirements.txt --upgrade
docker-compose down
docker-compose up --build
```

### Backup de Evaluaciones

```bash
# Las evaluaciones se guardan en:
# - Django: Base de datos (InterviewSession)
# - Logs: Container logs (docker logs)

# Backup de datos
docker exec django-db pg_dump evalyze > backup.sql
```

## Documentación de Referencia

- 📖 `AI_IMPROVEMENTS.md` - Detalles técnicos de cambios
- 📖 `CAMBIOS_IA_RESUMEN.md` - Resumen ejecutivo
- 📖 `GUIA_INTEGRACION_DJANGO.md` - Integración con backend
- 📖 `VALIDACION_CHECKLIST.md` - Checklist de validación
- 📖 `README_MEJORAS_IA.md` - Resumen visual

## Comunicación con el Equipo

Avisar a:
- [ ] **Backend (Django)** - Nuevos endpoints disponibles
- [ ] **Frontend (Angular)** - UI para mostrar SWOT
- [ ] **QA/Testing** - Suite de tests lista
- [ ] **DevOps** - Nuevos requisitos (más RAM/CPU)
- [ ] **HR/Reclutamiento** - Nuevo análisis SWOT disponible

## Commits Sugeridos

```bash
git add ai-service/main.py ai-service/validators.py
git commit -m "feat(ai-service): improved prompts and validation for llama3.2"

git add ai-service/test_endpoints.py  
git commit -m "test(ai-service): add comprehensive test suite"

git add ai-service/AI_IMPROVEMENTS.md
git commit -m "docs(ai-service): add detailed improvement documentation"

git add django-docker/jobs/services/interview_service.py
git commit -m "feat(interview): improve system prompt for linear interview flow"
```

## Timeline de Despliegue

| Tarea | Duración | Responsable |
|-------|----------|-------------|
| Preparación | 5 min | DevOps |
| Validación | 10 min | QA |
| Build Docker | 15 min | DevOps |
| Deploy | 5 min | DevOps |
| Tests | 10 min | QA |
| Verificación | 5 min | Tech Lead |
| **TOTAL** | **~50 minutos** | - |

---

## 🎊 Estado Final

✅ Código listo para producción
✅ Tests validados
✅ Documentación completa
✅ Procedimiento de despliegue definido

**Próximo paso:** Ejecutar despliegue en environment de staging primero

---

**Documento creado:** 2025-12-15
**Versión:** 1.0
**Estado:** ✅ LISTO PARA DESPLIEGUE
