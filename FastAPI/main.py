from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime


app = FastAPI(
    title="OmniSight CI/CD Webhook",
    description="Webhook service for the OmniSight UI self-healing automation project",
    version="1.0.0"
)


class WebhookRequest(BaseModel):
    event: str
    repository: str
    branch: str
    commit_id: str


class WebhookResponse(BaseModel):
    status: str
    message: str
    event: str
    repository: str
    branch: str
    commit_id: str
    received_at: str


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "OmniSight CI/CD Webhook",
        "message": "FastAPI server is running successfully"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "OmniSight CI/CD Webhook"
    }


@app.post("/webhook", response_model=WebhookResponse)
def webhook(data: WebhookRequest):
    return WebhookResponse(
        status="success",
        message="CI/CD webhook received successfully",
        event=data.event,
        repository=data.repository,
        branch=data.branch,
        commit_id=data.commit_id,
        received_at=datetime.now().isoformat()
    )