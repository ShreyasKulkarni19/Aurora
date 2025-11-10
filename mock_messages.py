"""Mock messages API for testing purposes."""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Sample messages data
MOCK_MESSAGES = {
    "total": 3349,
    "items": [
        {
            "id": "b1e9bb83-18be-4b90-bbb8-83b7428e8e21",
            "user_id": "cd3a350e-dbd2-408f-afa0-16a072f56d23",
            "user_name": "Sophia Al-Farsi",
            "timestamp": "2025-05-05T07:47:20.159073+00:00",
            "message": "Please book a private jet to Paris for this Friday."
        },
        {
            "id": "609ba052-c9e7-49e6-8b62-061eb8785b63",
            "user_id": "e35ed60a-5190-4a5f-b3cd-74ced7519b4a",
            "user_name": "Fatima El-Tahir",
            "timestamp": "2024-11-14T20:03:44.159235+00:00",
            "message": "Can you confirm my dinner reservation at The French Laundry for four people tonight?"
        },
        {
            "id": "44be0607-a918-40fa-a122-b2435fe54f3e",
            "user_id": "23103ae5-38a8-4d82-af82-e9942aa4aefb",
            "user_name": "Armand Dupont",
            "timestamp": "2025-03-09T02:25:23.159256+00:00",
            "message": "I need two tickets to the opera in Milan this Saturday."
        }
    ]
}

@app.get("/messages/")
async def get_messages(skip: int = 0, limit: int = 100):
    """Mock messages endpoint."""
    return MOCK_MESSAGES

if __name__ == "__main__":
    print("Starting mock messages API on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
