# Music Quiz Live 🎵 (Railway + Vercel)

Полноценное веб-приложение для проведения музыкальных квизов в реальном времени.

## Архитектура
* **`/backend` (Деплоится на Railway):**
  * Сервер на Python + FastAPI
  * Стриминг 20-секундных нарезок аудио MP3 и фото артистов
  * Хранилище готовых игр в `games/` (`Final_Quiz_Hard`, `Test_Quiz_Run`)
  * Автодеплой через Railway (Nixpacks / Procfile)
* **`/frontend` (Деплоится на Vercel):**
  * Интерактивное веб-табло (Vanilla JS / CSS)
  * Анимированный таймер на 20 секунд, виниловый диск, открытие карточек с фото
  * Сетка треков с отметкой сыгранных вопросов
  * Настройка подключения к API в один клик

---

## Локальный запуск на Mac

### 1. Запуск бэкенда (FastAPI)
```bash
cd /Users/vadisla/projects/quiz_web/backend
python3 -m pip install -r requirements.txt
python3 main.py
```
Бэкенд запустится на: `http://localhost:8000`  
Документация Swagger: `http://localhost:8000/docs`

### 2. Запуск фронтенда
Просто откройте в любом браузере:
`/Users/vadisla/projects/quiz_web/frontend/index.html`  
Или запустите через Python:
```bash
cd /Users/vadisla/projects/quiz_web/frontend
python3 -m http.server 3000
```
И откройте `http://localhost:3000`.

---

## Деплой в облако (Railway + Vercel)

### Шаг 1. Отправка в GitHub
```bash
cd /Users/vadisla/projects/quiz_web
git init
git add .
git commit -m "feat: initial commit of Music Quiz Live"
git remote add origin https://github.com/<ваш_логин>/quiz-web.git
git push -u origin main
```

### Шаг 2. Деплой бэкенда на Railway
1. Зайдите на [Railway.app](https://railway.app) ➔ **New Project** ➔ **Deploy from GitHub repo**.
2. Выберите репозиторий `quiz-web`.
3. В настройках проекта (Settings) установите:
   * **Root Directory:** `/backend`
4. В разделе **Networking** нажмите **Generate Domain** (получите адрес вида `https://quiz-web-production.up.railway.app`).

### Шаг 3. Деплой фронтенда на Vercel
1. Зайдите на [Vercel.com](https://vercel.com) ➔ **Add New...** ➔ **Project**.
2. Выберите репозиторий `quiz-web`.
3. В поле **Root Directory** укажите: `frontend`.
4. Нажмите **Deploy**.
5. Через 15 секунд ваш сайт будет доступен по ссылке `https://quiz-web.vercel.app`!
6. Откройте сайт, нажмите шестеренку ⚙️ и вставьте полученный URL из Railway.
