from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_router import router as ai_router

app = FastAPI(title="Evalyze Interview Service")

# CORS: agrega tu dominio de frontend (prod) y el de desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:9000", "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)


@app.get("/health")
def health():
    return {"status": "ok"}
