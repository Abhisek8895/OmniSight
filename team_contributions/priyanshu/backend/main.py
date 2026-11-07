from fastapi import FastAPI

app = FastAPI(title="UI Testing Webhook")

@app.get("/")
def home():
    return {"message": "UI Testing Webhook is running"}

@app.post("/webhook")
def receive_webhook(data: dict):
    return {
        "message": "Webhook received successfully",
        "data": data
    }
