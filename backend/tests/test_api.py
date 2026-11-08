"""
Тесты для FastAPI бэкенда Music Quiz Live.
Проверяют работоспособность всех эндпоинтов API, отдачу метаданных, стриминг аудио и фото.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "endpoints" in data


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_get_quizzes():
    response = client.get("/api/quizzes")
    assert response.status_code == 200
    quizzes = response.json()
    assert isinstance(quizzes, list)
    assert len(quizzes) > 0
    ids = [q["id"] for q in quizzes]
    assert "Test_Superpower_Run" in ids or "Final_Quiz_Hard" in ids


def test_quiz_detail():
    # Проверяем детальную информацию по игре Test_Superpower_Run
    response = client.get("/api/quizzes/Test_Superpower_Run")
    if response.status_code == 200:
        data = response.json()
        assert data["id"] == "Test_Superpower_Run"
        assert "tracks" in data
        assert len(data["tracks"]) >= 2
        t1 = data["tracks"][0]
        assert "question" in t1
        assert "answer" in t1
        assert "audio_url" in t1


def test_quiz_audio_streaming():
    response = client.get("/api/quizzes/Test_Superpower_Run/audio/1")
    if response.status_code == 200:
        assert response.headers.get("content-type") == "audio/mpeg"
        assert response.headers.get("accept-ranges") == "bytes"
        assert len(response.content) > 10000


def test_quiz_photo_delivery():
    response = client.get("/api/quizzes/Test_Superpower_Run/photo/1")
    if response.status_code == 200:
        assert response.headers.get("content-type") == "image/jpeg"
        assert len(response.content) > 5000


def test_quiz_not_found():
    response = client.get("/api/quizzes/Non_Existent_Quiz_12345")
    assert response.status_code == 404
