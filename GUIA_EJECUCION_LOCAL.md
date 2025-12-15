# 🚀 GUÍA DE EJECUCIÓN LOCAL - Evalyze-2025

## Ambiente Disponible

✅ Python 3.11.0
✅ pip 22.3
✅ npm 10.9.2
✅ node v22.16.0

## Opción 1: Ejecución Completa (Con Docker) - RECOMENDADO PARA PRODUCCIÓN

```bash
cd django-docker/
docker-compose up --build
```

Esto inicia:
- 🐘 PostgreSQL (BD)
- 🐍 Django (Backend en puerto 8000)
- 🤖 Ollama (LLM en puerto 11434)
- 🧠 AI Service (Servicio IA en puerto 8001)
- 🎨 Frontend Angular (Puerto 4200)

## Opción 2: Ejecución Local (Recomendado para desarrollo)

### 2.1 Instalar Dependencias

#### Backend (Django)
```bash
cd django-docker/
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### AI Service
```bash
cd ai-service/
pip install -r requirements.txt
```

#### Frontend (Angular)
```bash
cd Eva-Front/
npm install
# o si usas pnpm:
pnpm install
```

### 2.2 Iniciar Ollama (Requerido)

```bash
# Descargar e instalar desde https://ollama.ai/
# O si ya está instalado:
ollama serve
```

En otra terminal:
```bash
ollama pull llama3.2
```

### 2.3 Iniciar cada servicio en terminal separada

#### Terminal 1: AI Service
```bash
cd ai-service/
python main.py
```

#### Terminal 2: Django Backend
```bash
cd django-docker/
python manage.py runserver 0.0.0.0:8000
```

#### Terminal 3: Frontend
```bash
cd Eva-Front/
npm start
# o
pnpm start
```

### 2.4 Validar que todo funciona

```bash
# En otra terminal, ejecutar tests de IA
cd ai-service/
python test_endpoints.py
```

## Acceso a la Aplicación

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:4200 | Interfaz visual |
| Backend | http://localhost:8000/api | API REST |
| AI Service | http://localhost:8001 | Servicio de IA |
| Ollama | http://localhost:11434 | LLM |

## Primeros Pasos

1. **Abrir Frontend**
   ```
   http://localhost:4200
   ```

2. **Registrarse como empresa**
   - Email: empresa@test.com
   - Password: test123

3. **Crear vacante**
   - Título: Backend Engineer
   - Requisitos: Node.js, PostgreSQL

4. **Probar generador de preguntas**
   - El sistema generará 4 preguntas automáticamente

5. **Ver análisis SWOT**
   - Después de entrevista completada

## Troubleshooting

### Error: "Cannot find module"
```bash
pip install -r requirements.txt
```

### Error: "Port already in use"
```bash
# Cambiar puerto en:
# Django: manage.py runserver 0.0.0.0:8001
# Frontend: ng serve --port 4201
```

### Error: "Cannot connect to Ollama"
```bash
# Verificar que Ollama está corriendo
curl http://localhost:11434/api/tags
```

### Error: "No module named 'django'"
```bash
# Activar virtual environment
venv\Scripts\activate
pip install -r requirements.txt
```

## Variables de Entorno

Crear `.env` en `django-docker/`:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
OLLAMA_URL=http://localhost:11434/api/generate
AI_SERVICE_URL=http://localhost:8001
```

## Base de Datos

```bash
cd django-docker/

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser
```

## Comandos Útiles

```bash
# Ver estado de servicios
docker ps

# Ver logs
docker logs -f django-docker-web-1
docker logs -f django-docker-ai-service-1

# Limpiar cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -name "*.pyc" -delete

# Resetear base de datos
rm django-docker/db.sqlite3
python django-docker/manage.py migrate
```

## Performance Local

- Inicio total: ~30 segundos
- Primera consulta a IA: ~5-10 segundos (llama3.2 es lento)
- Análisis SWOT: ~10-15 segundos

## Logs Importantes

- Django: `localhost:8000` (terminal)
- AI Service: `localhost:8001/docs` (Swagger)
- Frontend: `localhost:4200` (consola del navegador)

---

**¡Listo para ejecutar!**
