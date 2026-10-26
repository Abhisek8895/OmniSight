from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="OmniSight CI/CD Webhook",
    description="Webhook service for the OmniSight UI self-healing automation project",
    version="1.0.0"
)


SUPPORTED_EVENTS = {
    "push": "Source code push received",
    "build": "Build process triggered",
    "test": "Test execution triggered",
    "deployment": "Deployment process triggered"
}


class WebhookRequest(BaseModel):
    event: str = Field(..., description="CI/CD event type")
    repository: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Git branch")
    commit_id: str = Field(..., description="Commit identifier")


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
        "service": "OmniSight CI/CD Webhook",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/events")
def supported_events():
    return {
        "supported_events": list(SUPPORTED_EVENTS.keys()),
        "total_events": len(SUPPORTED_EVENTS)
    }


@app.post("/webhook", response_model=WebhookResponse)
def webhook(data: WebhookRequest):

    event = data.event.lower()

    if event not in SUPPORTED_EVENTS:
        return WebhookResponse(
            status="rejected",
            message=f"Unsupported CI/CD event: {data.event}",
            event=data.event,
            repository=data.repository,
            branch=data.branch,
            commit_id=data.commit_id,
            received_at=datetime.now().isoformat()
        )

    return WebhookResponse(
        status="success",
        message=SUPPORTED_EVENTS[event],
        event=event,
        repository=data.repository,
        branch=data.branch,
        commit_id=data.commit_id,
        received_at=datetime.now().isoformat()
    )