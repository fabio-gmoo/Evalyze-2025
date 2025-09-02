from fastapi import FastAPI  # type: ignore

app = FastAPI(title="FastAPI Hello")


@app.get("/")
def hello():
    return {"message": "Hola desde FastAPI 🚀"}
