import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.api.v1.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

SESSION_ID = "test-session"
USER_ID = "test-user"
PAGE_URL = "https://example.com"

# Test session creation
def test_create_session():
    payload = {
        "session_id": SESSION_ID,
        "user_id": USER_ID,
        "page_url": PAGE_URL
    }
    response = client.post("/session/new", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"] == SESSION_ID
    assert "retriever_instance" in data

# Test sending a chat message
def test_chat():
    payload = {
        "message": "Hello!",
        "retriever": None,
        "session_id": SESSION_ID,
        "user_id": USER_ID
    }
    response = client.post(f"/c/{SESSION_ID}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["session_id"] == SESSION_ID
    assert data["user_id"] == USER_ID

# Test getting chat history
def test_get_history():
    payload = {
        "session_id": SESSION_ID,
        "user_id": USER_ID
    }
    response = client.get(f"/session/{SESSION_ID}/history", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert data["session_id"] == SESSION_ID
    assert data["user_id"] == USER_ID

# Test clearing chat history
def test_clear_history():
    payload = {
        "session_id": SESSION_ID,
        "user_id": USER_ID
    }
    response = client.post(f"/session/{SESSION_ID}/delete", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "History clean successfully"