from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_cloud_router import router as ai_router

app = FastAPI(title="Evalyze Interview Service")

# CORS: agrega tu dominio de frontend (prod) y el de desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://TU-DOMINIO-Frontend"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)

@app.get("/health")
def health():
    return {"status": "ok"}
