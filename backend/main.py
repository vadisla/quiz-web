import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

BASE_DIR = Path(__file__).resolve().parent
GAMES_DIR = BASE_DIR / "games"

app = FastAPI(
    title="Music Quiz Live API",
    description="Backend API for Music Quiz Live Board (Railway Deployment)",
    version="1.0.0"
)

# Enable CORS for Vercel and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_tracks_from_board_html(board_path: Path) -> List[Dict[str, Any]]:
    """Извлекает список треков из board.html игры"""
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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Music Quiz Live API",
        "endpoints": {
            "quizzes": "/api/quizzes",
            "quiz_detail": "/api/quizzes/{name}",
            "audio": "/api/quizzes/{name}/audio/{track_index}",
            "photo": "/api/quizzes/{name}/photo/{track_index}"
        }
    }

@app.get("/api/quizzes")
def get_quizzes():
    """Возвращает список всех доступных квизов"""
    quizzes = []
    if not GAMES_DIR.exists():
        return quizzes

    for game_folder in sorted(GAMES_DIR.iterdir()):
        if game_folder.is_dir() and not game_folder.name.startswith("."):
            board_file = game_folder / "board.html"
            tracks = extract_tracks_from_board_html(board_file)
            
            # Определяем примерную сложность и количество треков
            tracks_count = len(tracks)
            if tracks_count == 0:
                mp3_count = len(list(game_folder.glob("track*.mp3")))
                tracks_count = mp3_count

            quizzes.append({
                "id": game_folder.name,
                "name": game_folder.name.replace("_", " "),
                "folder": game_folder.name,
                "tracks_count": tracks_count,
                "has_board": board_file.exists()
            })
    return quizzes

@app.get("/api/quizzes/{name}")
def get_quiz_detail(name: str):
    """Возвращает подробные данные квиза с треками, вопросами и ответами"""
    game_folder = GAMES_DIR / name
    if not game_folder.exists() or not game_folder.is_dir():
        raise HTTPException(status_code=404, detail="Квиз не найден")

    board_file = game_folder / "board.html"
    raw_tracks = extract_tracks_from_board_html(board_file)

    tracks = []
    for t in raw_tracks:
        idx = t.get("index", 1)
        tracks.append({
            "index": idx,
            "question": t.get("question", f"Трек #{idx}"),
            "answer": t.get("answer", "Скрытый ответ"),
            "audio_url": f"/api/quizzes/{name}/audio/{idx}",
            "photo_url": f"/api/quizzes/{name}/photo/{idx}"
        })

    return {
        "id": name,
        "name": name.replace("_", " "),
        "total_tracks": len(tracks),
        "tracks": tracks
    }

@app.get("/api/quizzes/{name}/audio/{track_index}")
def get_quiz_audio(name: str, track_index: int):
    """Стримит 20-секундный аудиофрагмент трека"""
    game_folder = GAMES_DIR / name
    audio_file = game_folder / f"track{track_index}.mp3"
    
    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="Аудиофайл не найден")
        
    return FileResponse(
        path=str(audio_file),
        media_type="audio/mpeg",
        filename=f"track{track_index}.mp3"
    )

@app.get("/api/quizzes/{name}/photo/{track_index}")
def get_quiz_photo(name: str, track_index: int):
    """Отдает фото исполнителя для ответа"""
    game_folder = GAMES_DIR / name
    board_file = game_folder / "board.html"
    raw_tracks = extract_tracks_from_board_html(board_file)
    
    photo_rel_path = None
    for t in raw_tracks:
        if t.get("index") == track_index:
            photo_rel_path = t.get("photo")
            break
            
    if photo_rel_path:
        photo_file = game_folder / photo_rel_path
        if photo_file.exists():
            return FileResponse(path=str(photo_file), media_type="image/jpeg")

    # Поиск по шаблону в папке photos
    photos_dir = game_folder / "photos"
    if photos_dir.exists():
        for p in photos_dir.glob("*.jpg"):
            return FileResponse(path=str(p), media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="Фото не найдено")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
