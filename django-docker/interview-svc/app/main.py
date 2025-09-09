from fastapi import FastAPI  # type: ignore

<<<<<<< Updated upstream:django-docker/interview-svc/main.py
app = FastAPI(title="FastAPI Hello")


@app.get("/")
def hello():
    return {"message": "Hola desde FastAPI 🚀"}
=======
app = FastAPI(title="Evalyze Interview Service")

# CORS: para desarrollo (en producción lista los dominios de tu front)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# /ai/health y /ai/chat
app.include_router(ai_router)
>>>>>>> Stashed changes:django-docker/interview-svc/app/main.py
