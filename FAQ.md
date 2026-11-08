# FAQ: Music Quiz Live (Production)

## 1. Что это за проект и где он развернут?
**Music Quiz Live** — веб-платформа для проведения интерактивных музыкальных квизов в реальном времени.

### Продакшен-ссылки:
- 🌐 **Фронтенд (Веб-табло):** [https://music-quiz-live.vercel.app](https://music-quiz-live.vercel.app)
- 🚀 **Бэкенд (FastAPI API):** [https://backend-production-4042.up.railway.app](https://backend-production-4042.up.railway.app)
- 🐙 **Репозиторий GitHub:** [https://github.com/vadisla/quiz-web](https://github.com/vadisla/quiz-web)

---

## 2. Архитектура: как устроена система?

```
┌────────────────────────────────────────────────────────┐
│             1. КОНТУР ПОДГОТОВКИ (CLI на Mac)          │
│            /Users/vadisla/projects/quiz                │
├────────────────────────────────────────────────────────┤
│ • Вход: текстовый файл с артистами                     │
│ • Spotify API + Yandex Music API (подбор треков)       │
│ • yt-dlp + Deezer API fallback (скачивание аудио)      │
│ • trimaudio2.py + ffmpeg (нарезка 20с клипов с фейдами)│
│ • normalize_loudness.py (EBU R128 нормализация)        │
│ • artist_photo_search (Smart Crop 800x600 лиц)         │
│ • QuizBuilder -> quiz.json, questions.txt, answers.txt │
│ • Авто-синхронизация в quiz_web/backend/games/         │
└───────────────────────────┬────────────────────────────┘
                            │ (git push в GitHub)
                            ▼
┌────────────────────────────────────────────────────────┐
│             2. КОНТУР ДЕМОНСТРАЦИИ (Облако)            │
├───────────────────────────┬────────────────────────────┤
│     БЭКЕНД (Railway)      │     ФРОНТЕНД (Vercel)      │
│                           │                            │
│ • Python + FastAPI        │ • Vanilla JS + CSS3        │
│ • Автодеплой при push     │ • Анимированный винил      │
│ • HTTP Range 206 стриминг │ • Таймер на 20 секунд      │
│ • Раздача фото и JSON     │ • Карточки ответов и фото  │
└───────────────────────────┴────────────────────────────┘
```

---

## 3. Как создать новый квиз и отправить его на сайт?

1. Откройте терминал на Mac:
   ```bash
   cd /Users/vadisla/projects/quiz
   ./venv/bin/python main.py create
   ```
2. Введите название квиза и перетащите TXT-файл со списком исполнителей.
3. Программа автоматически:
   - Подберет треки по сложности (хиты топ-3 / средние / редкие);
   - Скачает аудио (через YouTube или официальный Deezer preview);
   - Нарежет ровно 20-секундные отрывки с фейдами;
   - Выровняет общую громкость всех треков;
   - Скачает и центрирует фото артистов (800x600);
   - Сгенерирует `quiz.json` и скопирует папку в `/Users/vadisla/projects/quiz_web/backend/games/`.
4. Опубликуйте новую игру в облако одной командой:
   ```bash
   cd /Users/vadisla/projects/quiz_web
   git add backend/games
   git commit -m "feat: add new quiz"
   git push origin main
   ```
   Railway автоматически подхватит изменения, пересоберет сервис, и через 1-2 минуты новый квиз появится на [https://music-quiz-live.vercel.app](https://music-quiz-live.vercel.app)!

---

## 4. Как запустить проект локально?

### Запуск бэкенда:
```bash
cd /Users/vadisla/projects/quiz_web/backend
./venv/bin/python main.py
```
Сервер запустится на `http://localhost:8000`. Документация Swagger: `http://localhost:8000/docs`.

### Запуск фронтенда:
Просто откройте файл `/Users/vadisla/projects/quiz_web/frontend/index.html` в любом браузере, либо запустите локальный веб-сервер:
```bash
cd /Users/vadisla/projects/quiz_web/frontend
python3 -m http.server 3000
```
И откройте `http://localhost:3000`.

---

## 5. Где хранятся ключи и токены?
Все API-ключи (Spotify, Yandex) хранятся исключительно на локальном Mac в `~/scripts_rules/keys/` и **никогда не коммитятся в git**. Сервер Railway в облаке работает автономно, отдавая уже готовые сгенерированные файлы игр.
