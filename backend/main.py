"""
Music Quiz Live API: FastAPI сервер для веб-табло квиза.
Обслуживает эндпоинты списка игр, метаданных квизов, стриминга 20-секундного аудио
с поддержкой HTTP Range и раздачи фотографий артистов.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

BASE_DIR = Path(__file__).resolve().parent
GAMES_DIR = BASE_DIR / "games"

app = FastAPI(
    title="Music Quiz Live API",
    description="Backend API for Music Quiz Live Board (Railway Deployment)",
    version="1.1.0"
)

# Настройка CORS для Vercel и локальной разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_tracks_from_board_html(board_path: Path) -> List[Dict[str, Any]]:
    """Извлекает список треков из board.html игры (fallback для старых квизов)."""
    if not board_path.exists():
        return []
    content = board_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"const\s+tracks\s*=\s*(\[.*?\]);", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return []


def get_quiz_manifest(game_folder: Path) -> Optional[Dict[str, Any]]:
    """Загружает структурированный манифест квиза из quiz.json или board.html."""
    quiz_json_file = game_folder / "quiz.json"
    if quiz_json_file.exists():
        try:
            with open(quiz_json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass

    # Fallback на board.html
    board_file = game_folder / "board.html"
    if board_file.exists():
        raw_tracks = extract_tracks_from_board_html(board_file)
        tracks = []
        for t in raw_tracks:
            idx = t.get("index", 1)
            tracks.append({
                "index": idx,
                "artist": t.get("artist", ""),
                "title": t.get("title", ""),
                "question": t.get("question", f"Трек #{idx}"),
                "answer": t.get("answer", "Скрытый ответ"),
                "audio_url": f"/api/quizzes/{game_folder.name}/audio/{idx}",
                "photo_url": f"/api/quizzes/{game_folder.name}/photo/{idx}",
                "photo_file": t.get("photo")
            })
        return {
            "id": game_folder.name,
            "name": game_folder.name.replace("_", " "),
            "total_tracks": len(tracks),
            "tracks": tracks
        }

    return None


@app.get("/")
def read_root():
    """Корневой эндпоинт проверки сервиса."""
    return {
        "status": "online",
        "service": "Music Quiz Live API",
        "version": "1.1.0",
        "endpoints": {
            "health": "/api/health",
            "quizzes": "/api/quizzes",
            "quiz_detail": "/api/quizzes/{name}",
            "audio": "/api/quizzes/{name}/audio/{track_index}",
            "photo": "/api/quizzes/{name}/photo/{track_index}"
        }
    }


@app.get("/api/health")
def healthcheck():
    """Эндпоинт для Railway healthcheck / ping мониторинга."""
    return {"status": "ok", "service": "Music Quiz Live API"}


@app.get("/api/quizzes")
def get_quizzes():
    """Возвращает список всех доступных квизов."""
    quizzes = []
    if not GAMES_DIR.exists():
        return quizzes

    for game_folder in sorted(GAMES_DIR.iterdir()):
        if game_folder.is_dir() and not game_folder.name.startswith("."):
            manifest = get_quiz_manifest(game_folder)
            tracks_count = 0
            if manifest and "tracks" in manifest:
                tracks_count = len(manifest["tracks"])
            else:
                tracks_count = len(list(game_folder.glob("track*.mp3")))

            quizzes.append({
                "id": game_folder.name,
                "name": game_folder.name.replace("_", " "),
                "folder": game_folder.name,
                "tracks_count": tracks_count,
                "has_manifest": (game_folder / "quiz.json").exists(),
                "has_board": (game_folder / "board.html").exists()
            })
    return quizzes


@app.get("/api/quizzes/{name}")
def get_quiz_detail(name: str):
    """Возвращает подробные данные квиза с треками, вопросами и ответами."""
    game_folder = GAMES_DIR / name
    if not game_folder.exists() or not game_folder.is_dir():
        raise HTTPException(status_code=404, detail="Квиз не найден")

    manifest = get_quiz_manifest(game_folder)
    if not manifest:
        raise HTTPException(status_code=404, detail="Манифест квиза не найден")

    return manifest


@app.get("/api/quizzes/{name}/audio/{track_index}")
def get_quiz_audio(name: str, track_index: int, request: Request):
    """
    Стримит 20-секундный аудиофрагмент трека с поддержкой заголовка Range (HTTP 206)
    для мгновенной буферизации и совместимости со всеми браузерами (Safari/Chrome/iOS).
    """
    game_folder = GAMES_DIR / name
    audio_file = game_folder / f"track{track_index}.mp3"

    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="Аудиофайл не найден")

    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=86400"
    }

    return FileResponse(
        path=str(audio_file),
        media_type="audio/mpeg",
        filename=f"track{track_index}.mp3",
        headers=headers
    )


@app.get("/api/quizzes/{name}/photo/{track_index}")
def get_quiz_photo(name: str, track_index: int):
    """Отдает кадрированное фото исполнителя (800x600) для карточки ответа."""
    game_folder = GAMES_DIR / name
    if not game_folder.exists() or not game_folder.is_dir():
        raise HTTPException(status_code=404, detail="Квиз не найден")

    manifest = get_quiz_manifest(game_folder)
    photo_rel_path = None

    if manifest and "tracks" in manifest:
        for t in manifest["tracks"]:
            if t.get("index") == track_index:
                photo_rel_path = t.get("photo_file") or t.get("photo")
                break

    if photo_rel_path:
        photo_file = game_folder / photo_rel_path
        if photo_file.exists():
            return FileResponse(
                path=str(photo_file),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"}
            )

    # Fallback: поиск по шаблону в папке photos
    photos_dir = game_folder / "photos"
    if photos_dir.exists():
        photos = list(photos_dir.glob("*.jpg"))
        if photos:
            # Берем фото по индексу трека с зацикливанием
            chosen = photos[(track_index - 1) % len(photos)]
            return FileResponse(
                path=str(chosen),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=86400"}
            )

    raise HTTPException(status_code=404, detail="Фото не найдено")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
