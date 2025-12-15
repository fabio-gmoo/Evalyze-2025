# 🎬 GUÍA RÁPIDA DE INICIO - Evalyze-2025

## ¡IMPORTANTE ANTES DE COMENZAR!

✅ Asegúrate de tener instalado **Ollama**:
   - Descargar desde: https://ollama.ai/
   - Instalar y ejecutar
   - En terminal nueva ejecutar: `ollama pull llama3.2`

---

## 📋 PASO 1: Preparar el Entorno

### 1.1 Abrir PowerShell como Administrador

Presiona `Win + X` y selecciona "Windows PowerShell (Admin)"

### 1.2 Navegar al proyecto
```powershell
cd "c:\Users\joaqu\OneDrive\Documents\Ingeniería_Sistemas\Taller_sisinfo\Evalyze-2025"
```

### 1.3 Preparar Django
```powershell
cd django-docker
python manage.py migrate
cd ..
```

---

## 🚀 PASO 2: Iniciar Servicios (4 TERMINALES SEPARADAS)

### Terminal 1: Ollama (DEBE ESTAR CORRIENDO PRIMERO)
```powershell
ollama serve
```

Espera a ver: `Listening on 127.0.0.1:11434`

### Terminal 2: AI Service
```powershell
cd "c:\Users\joaqu\OneDrive\Documents\Ingeniería_Sistemas\Taller_sisinfo\Evalyze-2025\ai-service"
python main.py
```

Espera a ver: `INFO:     Application startup complete [uvicorn] Uvicorn running on http://0.0.0.0:8001`

### Terminal 3: Django Backend
```powershell
cd "c:\Users\joaqu\OneDrive\Documents\Ingeniería_Sistemas\Taller_sisinfo\Evalyze-2025\django-docker"
python manage.py runserver
```

Espera a ver: `Starting development server at http://127.0.0.1:8000/`

### Terminal 4: Angular Frontend
```powershell
cd "c:\Users\joaqu\OneDrive\Documents\Ingeniería_Sistemas\Taller_sisinfo\Evalyze-2025\Eva-Front"
npm start
```

Espera a ver: `Application bundle generation complete.`

---

## ✅ PASO 3: Verificar que Todo Funciona

Abre en el navegador:

1. **Frontend**: http://localhost:4200
   - Debe mostrar página de login de Evalyze

2. **Backend API**: http://localhost:8000/api/
   - Debe mostrar JSON con opciones de API

3. **AI Service**: http://localhost:8001/
   - Debe mostrar estado del servicio

4. **Tests de IA** (en terminal separada):
   ```powershell
   cd "c:\Users\joaqu\OneDrive\Documents\Ingeniería_Sistemas\Taller_sisinfo\Evalyze-2025\ai-service"
   python test_endpoints.py
   ```

---

## 🎮 PASO 4: Usar la Aplicación

### 4.1 Acceder al Frontend
```
http://localhost:4200
```

### 4.2 Registrarse
- **Como Empresa:**
  - Email: empresa@test.com
  - Password: test123
  - Rol: Empresa

### 4.3 Crear Vacante
1. Click en "Nueva Vacante"
2. Llenar datos:
   - Puesto: Backend Engineer
   - Empresa: Tu empresa
   - Requisitos: Node.js, PostgreSQL, REST APIs
3. Click "Crear"

### 4.4 Generar Preguntas de Entrevista
- El sistema genera automáticamente 4 preguntas
- Ver en sección "Preguntas de Entrevista"

### 4.5 Simular Entrevista de Candidato
- Registrarse como Candidato
- Aplicar a vacante
- Participar en entrevista
- El sistema generará análisis SWOT

### 4.6 Ver Análisis SWOT
- Como Empresa: Ver en "Reportes"
- Debe mostrar: Fortalezas, Debilidades, Oportunidades, Amenazas
- Con puntuaciones respaldadas por datos

---

## 🔧 TROUBLESHOOTING

### ❌ Error: "ModuleNotFoundError: No module named X"
```powershell
pip install -r requirements.txt
```

### ❌ Error: "Port 8000 already in use"
```powershell
python manage.py runserver 0.0.0.0:8001
```

### ❌ Error: "Cannot connect to Ollama"
- Verificar que Ollama está corriendo
- En terminal: `curl http://localhost:11434/api/tags`
- Debe retornar JSON con modelos

### ❌ Error: "Cannot connect to AI Service"
- Verificar que terminal de AI Service está corriendo
- Ver logs en esa terminal

### ❌ Error: "Cannot connect to Django"
- Verificar que terminal de Django está corriendo
- Ver logs en esa terminal

### ❌ El frontend no carga
- Limpiar cache del navegador (Ctrl+Shift+Delete)
- Recargar página (Ctrl+F5)
- Verificar que npm start finalizó correctamente

---

## 📊 URLs de Referencia

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:4200 | Interfaz visual |
| **Backend** | http://localhost:8000 | API REST |
| **Admin Django** | http://localhost:8000/admin | Administración |
| **AI Service** | http://localhost:8001 | Servicio IA |
| **AI Docs** | http://localhost:8001/docs | Swagger API |
| **Ollama** | http://localhost:11434 | LLM local |

---

## 📝 LOGS Y DEBUGGING

Mantén las terminales abiertas para ver logs en tiempo real:
- **Ollama**: Ver respuesta a consultas
- **AI Service**: Ver generación de preguntas/análisis
- **Django**: Ver peticiones HTTP
- **Frontend**: Abrir DevTools (F12) para ver console

---

## ⏱️ TIEMPOS ESPERADOS

- Inicio de Ollama: 5 segundos
- Inicio de AI Service: 10 segundos
- Inicio de Django: 5 segundos
- Inicio de Frontend: 20 segundos
- **Total inicial**: ~40 segundos

- Primera consulta a IA (generación): 5-10 segundos
- Generación de SWOT: 10-15 segundos

---

## 🎯 PRÓXIMOS PASOS DESPUÉS DE VERIFICAR

1. ✅ Ver que Frontend carga correctamente
2. ✅ Registrar empresa
3. ✅ Crear vacante
4. ✅ Ver preguntas generadas
5. ✅ Ejecutar test_endpoints.py
6. ✅ Revisar logs para ver prompts mejorados

---

## 💡 NOTAS IMPORTANTES

- **NO cierres las ventanas de terminal** mientras quieras usar la app
- Cada terminal mantiene un servicio corriendo
- Si cierras una, ese servicio se detiene
- Para detener todo, cierra todas las ventanas

---

**¡Listo! Si tienes dudas, revisa la sección TROUBLESHOOTING**
