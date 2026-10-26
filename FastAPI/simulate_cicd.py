import requests

WEBHOOK_URL = "http://127.0.0.1:8000/webhook"

events = [
    "push",
    "build",
    "test",
    "deployment"
]

for event in events:
    payload = {
        "event": event,
        "repository": "OmniSight",
        "branch": "main",
        "commit_id": "abc123"
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload
    )

    print(f"\nEvent: {event}")
    print("Status Code:", response.status_code)
    print("Response:", response.json())