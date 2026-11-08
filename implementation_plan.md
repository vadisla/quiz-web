# Music Quiz Live & Quiz Engine: План реализации и деплоя

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Довести генератор квизов (`/Users/vadisla/projects/quiz`) до полностью рабочего и задокументированного состояния, а веб-платформу (`/Users/vadisla/projects/quiz_web`) — до продакшен-деплоя на GitHub + Railway + Vercel с проверенным воспроизведением звука и фото.

**Architecture:** 
1. **Генерация игр (CLI на Mac):** Локальный Python-генератор подбирает треки через Spotify/Yandex API, скачивает аудио (yt-dlp с Deezer-fallback), нарезает 20-секундные хайлайты через `trimaudio2.py` / `ffmpeg`, нормализует громкость, находит и кадрирует фото артистов (800x600) и сохраняет игру в структурированном виде (`quiz.json`, `board.html`, mp3, фото).
2. **Бэкенд (Railway):** Легковесный FastAPI-сервис, раздающий метаданные игр, стримящий аудиофрагменты с поддержкой HTTP Range (для быстрой перемотки и мгновенного воспроизведения на мобильных и десктопных браузерах) и отдающий фото.
3. **Фронтенд (Vercel):** Статическое веб-приложение на чистом JS/CSS, подключающееся к публичному API бэкенда Railway, с виниловым проигрывателем, 20-секундным анимированным таймером, сеткой сыгранных вопросов и карточкой ответов.

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, SQLite, Spotipy, Yandex Music API, yt-dlp, ffmpeg/ffprobe, Pillow, Vanilla HTML5/CSS3/JavaScript, Railway CLI/MCP, Vercel CLI/Plugin, GitHub CLI (`gh`).

**Spec:** Документы правил `/Users/vadisla/projects/quiz/AGENTS.md` и `/Users/vadisla/projects/quiz_web/README.md`.

## Global Constraints

- **Строгое соблюдение изоляции секретов:** Никаких API-ключей, токенов и паролей в git-репозитории. Все ключи читаются исключительно из `~/scripts_rules/keys/`.
- **Без несанкционированного рефакторинга:** Менять только то, что необходимо для стабильной работы и исправления ошибок; соседние скрипты не ломать.
- **Подробное комментирование и документация:** Прямо в коде каждого модуля генератора указывать, какие внешние инструменты и библиотеки за что отвечают, откуда берутся зависимости. По итогам составить `FAQ.md`.
- **Язык общения и интерфейса:** Русский.

## Review Focus

1. **Сетевые сбои и rate limits аудио-сервисов:** При падении или блокировке yt-dlp должен надежно срабатывать fallback на Deezer preview без краха всего процесса генерации.
2. **Аудио-стриминг и совместимость с браузерами (Safari/Chrome/iOS):** Эндпоинт отдачи аудио на бэкенде должен корректно отдавать заголовки `Accept-Ranges: bytes` и статус `206 Partial Content`, иначе браузеры не могут плавно перематывать или повторно играть трек.
3. **Безопасность git:** Репозиторий перед отправкой в GitHub должен быть проверен на отсутствие скрытых токенов, логов и файлов `.env`.
4. **Связь фронтенда и бэкенда:** Проверка CORS (`*` или домен Vercel) и авто-подстановка URL Railway на Vercel без необходимости ручного ввода в ⚙️ при первом открытии.

---

### Task 1: Ревизия и исправление CLI машины подготовки квизов (`/Users/vadisla/projects/quiz`)

**Files:**
- Modify: `/Users/vadisla/projects/quiz/config.py`
- Modify: `/Users/vadisla/projects/quiz/core/track_selector.py`
- Modify: `/Users/vadisla/projects/quiz/core/downloader.py`
- Modify: `/Users/vadisla/projects/quiz/core/audio_processor.py`
- Modify: `/Users/vadisla/projects/quiz/core/quiz_builder.py`
- Modify: `/Users/vadisla/projects/quiz/generators/photo_finder.py`
- Modify: `/Users/vadisla/projects/quiz/main.py`
- Create: `/Users/vadisla/projects/quiz/FAQ.md`
- Test: `/Users/vadisla/projects/quiz/tests/test_quiz.py`

**Steps:**
- [ ] 1.1. Добавить подробные docstrings и комментарии в заголовках и методах каждого файла (`track_selector.py`, `downloader.py`, `audio_processor.py`, `photo_finder.py`, `quiz_builder.py`, `main.py`) с явным указанием:
  - Назначение инструмента;
  - Какие сторонние скрипты вызываются (из `~/scripts/audio_tools`, `~/scripts/artist_photo_search`, `~/scripts/deezerpreview`);
  - Какие API и ключи используются.
- [ ] 1.2. Проверить и исправить `track_selector.py`:
  - Проверить загрузку ключей Spotify (`SPOTIFY_CLIENT_ID.txt`, `SPOTIFY_CLIENT_SECRET.txt`) и Яндекс токена (`YANDEX_TOKEN.txt`).
  - Обеспечить корректный откат при отсутствии интернета или лимитах.
- [ ] 1.3. Проверить и усилить `downloader.py`:
  - Уточнить параметры вызова `yt-dlp` (добавить опции `--no-check-certificates`, таймауты, проверку размера скачанного файла).
  - Проверить fallback на `deezerpreview` и обеспечить, чтобы сбой скачивания одного трека не ронял всю сборку квиза.
- [ ] 1.4. Проверить и исправить `audio_processor.py`:
  - Проверить вызовы `trimaudio2.py` и ручного fallback на `ffmpeg`.
  - Устранить проблемы с путями при ручной нарезке коротких превью (Deezer 30c -> 20c с фейдами).
  - Проверить выравнивание громкости через `normalize_loudness.py`.
- [ ] 1.5. Доработать `quiz_builder.py`:
  - Помимо `questions.txt` и `answers.txt`, генерировать чистый JSON-файл игры `quiz.json` (содержащий структурированные данные о треках, артистах, названиях, вопросах, аудиофайлах и фото).
  - Добавить параметр/команду для прямой синхронизации (копирования) готовой игры в директорию `/Users/vadisla/projects/quiz_web/backend/games/<quiz_name>`.
- [ ] 1.6. Создать документацию `/Users/vadisla/projects/quiz/FAQ.md` с описанием пайплайна, используемых инструментов, частых ошибок и способов их решения.
- [ ] 1.7. Провести тестовый прогон:
  - Создать тестовый список из 2 исполнителей (`test_mini.txt`: Queen, Сплин).
  - Запустить генерацию квиза `Test_Superpower_Run`.
  - Проверить создание MP3-клипов 20с, фото 800x600, `quiz.json` и `board.html`.
  - Убедиться в отсутствии ошибок в логах `~/scripts_logs/quiz/quiz.log`.

---

### Task 2: Верификация и доработка веб-платформы (`/Users/vadisla/projects/quiz_web`)

**Files:**
- Modify: `/Users/vadisla/projects/quiz_web/backend/main.py`
- Modify: `/Users/vadisla/projects/quiz_web/frontend/app.js`
- Modify: `/Users/vadisla/projects/quiz_web/frontend/index.html`
- Create: `/Users/vadisla/projects/quiz_web/backend/tests/test_api.py`

**Steps:**
- [ ] 2.1. Доработать эндпоинты в `backend/main.py`:
  - Добавить чтение `quiz.json` с плавным fallback на парсинг `board.html` для старых квизов.
  - Реализовать стриминг аудио с поддержкой `Range` заголовков (206 Partial Content) для мгновенной буферизации и совместимости с мобильными браузерами.
  - Добавить эндпоинт `/api/health` для проверки статуса сервиса.
- [ ] 2.2. Написать тесты API `backend/tests/test_api.py` с использованием `TestClient` FastAPI:
  - Проверка получения списка квизов `/api/quizzes`.
  - Проверка деталей квиза `/api/quizzes/{name}`.
  - Проверка стриминга аудио и отдачи фото.
- [ ] 2.3. Доработать `frontend/app.js`:
  - Добавить дефолтный production fallback для Railway URL, чтобы пользователю не требовалось обязательно открывать шестеренку на проде.
  - Проверить корректность сброса аудио, таймера (20 сек), анимации вращения винила и отображения карточки ответа с фото.
- [ ] 2.4. Запустить локальный тестовый сервер FastAPI и открыть веб-интерфейс:
  - Убедиться, что звук проигрывается, таймер считает 20 секунд, фото отображается корректно.

---

### Task 3: Аудит безопасности и публикация кода в GitHub

**Files:**
- Modify: `/Users/vadisla/projects/quiz_web/.gitignore`
- Check: Весь репозиторий `quiz_web`

**Steps:**
- [ ] 3.1. Провести полный аудит `.gitignore`:
  - Убедиться, что игнорируются `venv/`, `.env`, `*.env`, `keys/`, `*.key`, `*.pem`, `*.log`, `__pycache__/`, `.DS_Store`, временные файлы.
  - Проверить историю коммитов на отсутствие случайных секретов.
- [ ] 3.2. Авторизовать GitHub CLI (`gh auth status` / токен или git SSH/HTTPS).
- [ ] 3.3. Создать удаленный репозиторий на GitHub (например, `vadisla/quiz-web` или аналогичное имя) и отправить ветку `main`.

---

### Task 4: Деплой бэкенда на Railway через Railway MCP

**Files:**
- Modify: `/Users/vadisla/projects/quiz_web/backend/railway.json`
- Modify: `/Users/vadisla/projects/quiz_web/backend/Procfile`

**Steps:**
- [ ] 4.1. С помощью `railway_mcp` создать проект в Railway (или подключить репозиторий GitHub).
- [ ] 4.2. Настроить сервис для бэкенда:
  - Указать корневую папку `/backend`.
  - Настроить команду запуска: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- [ ] 4.3. Сгенерировать публичный домен (`list-domains` / `generate-domain`).
- [ ] 4.4. Дождаться развертывания (`list-deployments`, `get-status`) и проверить логи (`get-logs`).
- [ ] 4.5. Проверить работу живого API по публичному адресу Railway (`curl https://.../api/quizzes`).

---

### Task 5: Деплой фронтенда на Vercel через Vercel-плагин

**Files:**
- Modify: `/Users/vadisla/projects/quiz_web/frontend/vercel.json`
- Modify: `/Users/vadisla/projects/quiz_web/frontend/app.js`

**Steps:**
- [ ] 5.1. Установить полученный production URL бэкенда Railway в качестве базового адреса для фронтенда.
- [ ] 5.2. Развернуть папку `/frontend` на Vercel (через плагин Vercel или Vercel CLI).
- [ ] 5.3. Получить публичный URL (например, `https://quiz-web-xxx.vercel.app`).
- [ ] 5.4. Проверить доступность сайта и заголовки ответа.

---

### Task 6: Финальная интеграция, E2E тестирование и документация

**Files:**
- Create: `/Users/vadisla/projects/quiz_web/FAQ.md`
- Modify: `/Users/vadisla/projects/quiz_web/README.md`

**Steps:**
- [ ] 6.1. Провести проверку сквозного сценария через браузер:
  - Открытие продакшен-ссылки Vercel.
  - Загрузка списка квизов из живого Railway API.
  - Запуск игры: воспроизведение 20-секундного аудиофрагмента из облака.
  - Остановка таймера, нажатие "Показать ответ", загрузка фото артиста и правильного ответа.
  - Переход к следующему вопросу.
- [ ] 6.2. Написать `FAQ.md` в корне `quiz_web`:
  - Архитектура решения (локальная машина подготовки + Railway + Vercel).
  - Инструкция по добавлению новых квизов.
  - Управление деплоями и обновление версий.
- [ ] 6.3. Обновить `README.md` с актуальными продакшен-ссылками.
