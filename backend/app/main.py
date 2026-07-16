from fastapi import FastAPI

app = FastAPI(
    title="Fruit Store Chatbot API",
    description="API para consultar o estoque de uma loja de frutas.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
