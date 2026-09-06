from fastapi import FastAPI

app = FastAPI(
    title="Agentic Job Intelligence API",
    description="AI-powered job intelligence and application platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Agentic Job Intelligence API is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }