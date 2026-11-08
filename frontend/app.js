// Music Quiz Live - Frontend Logic

// Configuration: API Base URL
// Автоматическое переключение: localhost для локальной разработки или продакшен Railway
const DEFAULT_PROD_API = "https://quiz-web-production.up.railway.app";
let API_URL = localStorage.getItem("quiz_api_url");

if (!API_URL) {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
        API_URL = "http://localhost:8000";
    } else {
        API_URL = DEFAULT_PROD_API;
    }
}

// App State
let currentQuiz = null;
let currentTrackIndex = null;
let playedTracks = new Set();
let timerInterval = null;

// DOM Elements
const connectionBadge = document.getElementById("connection-badge");
const apiConfigBtn = document.getElementById("api-config-btn");
const apiModal = document.getElementById("api-modal");
const apiUrlInput = document.getElementById("api-url-input");
const saveApiBtn = document.getElementById("save-api-btn");
const closeModalBtn = document.getElementById("close-modal-btn");

const lobbyView = document.getElementById("lobby-view");
const gameView = document.getElementById("game-view");
const quizList = document.getElementById("quiz-list");

const backToLobbyBtn = document.getElementById("back-to-lobby-btn");
const currentQuizTitle = document.getElementById("current-quiz-title");
const gameProgress = document.getElementById("game-progress");
const resetGameBtn = document.getElementById("reset-game-btn");

const questionCard = document.getElementById("question-card");
const answerCard = document.getElementById("answer-card");
const questionText = document.getElementById("question-text");
const vinylDisc = document.getElementById("vinyl-disc");
const timerCount = document.getElementById("timer-count");
const progressBarFill = document.getElementById("progress-bar-fill");
const playPauseBtn = document.getElementById("play-pause-btn");
const replayBtn = document.getElementById("replay-btn");
const revealBtn = document.getElementById("reveal-btn");

const artistPhoto = document.getElementById("artist-photo");
const answerText = document.getElementById("answer-text");
const answerReplayBtn = document.getElementById("answer-replay-btn");
const nextTrackBtn = document.getElementById("next-track-btn");

const tracksGrid = document.getElementById("tracks-grid");
const audioPlayer = document.getElementById("audio-player");

// --- API Connection & Healthcheck ---
async function checkApiConnection() {
    connectionBadge.className = "badge badge-warning";
    connectionBadge.textContent = "Проверка API...";

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);

    try {
        const res = await fetch(`${API_URL}/api/health`, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
            connectionBadge.className = "badge badge-success";
            connectionBadge.textContent = "🟢 API Онлайн";
            loadQuizzes();
        } else {
            throw new Error(`API status ${res.status}`);
        }
    } catch (err) {
        clearTimeout(timeoutId);
        connectionBadge.className = "badge badge-warning";
        connectionBadge.textContent = "🔴 Офлайн (нажмите ⚙️)";
        quizList.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 2rem;">
                <p style="color: var(--danger); font-weight: 700;">Не удалось подключиться к API по адресу:</p>
                <code style="background: #090d16; padding: 0.3rem 0.6rem; border-radius: 6px; display: inline-block; margin: 0.5rem 0;">${API_URL}</code>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.5rem;">
                    Запустите локальный бэкенд на порту 8000 или настройте актуальный адрес Railway в ⚙️
                </p>
                <button class="btn btn-secondary" style="margin-top: 1rem;" onclick="apiConfigBtn.click()">Открыть настройки ⚙️</button>
            </div>
        `;
    }
}

// --- Load Quiz List (Lobby) ---
async function loadQuizzes() {
    try {
        const res = await fetch(`${API_URL}/api/quizzes`);
        const data = await res.json();

        if (!data || data.length === 0) {
            quizList.innerHTML = `<p style="grid-column: 1/-1; text-align: center;">В базе пока нет готовых квизов</p>`;
            return;
        }

        quizList.innerHTML = "";
        data.forEach(q => {
            const card = document.createElement("div");
            card.className = "quiz-card";
            card.innerHTML = `
                <div>
                    <h3 class="quiz-card-title">${q.name}</h3>
                    <div class="quiz-card-meta">
                        <span>🎵 ${q.tracks_count} треков</span>
                        <span>•</span>
                        <span>Готов к игре</span>
                    </div>
                </div>
                <button class="btn btn-primary" onclick="startQuiz('${q.id}')">Запустить игру ▶</button>
            `;
            quizList.appendChild(card);
        });
    } catch (err) {
        console.error("Ошибка загрузки квизов:", err);
    }
}

// --- Start Selected Quiz ---
window.startQuiz = async function(quizId) {
    try {
        const res = await fetch(`${API_URL}/api/quizzes/${quizId}`);
        if (!res.ok) throw new Error("Квиз не найден");
        currentQuiz = await res.json();
        playedTracks.clear();

        currentQuizTitle.textContent = currentQuiz.name;
        lobbyView.classList.add("hidden");
        gameView.classList.remove("hidden");

        renderTracksGrid();
        selectTrack(1);
    } catch (err) {
        alert("Ошибка загрузки данных квиза: " + err.message);
    }
};

// --- Render Bottom Track Grid ---
function renderTracksGrid() {
    tracksGrid.innerHTML = "";
    if (!currentQuiz || !currentQuiz.tracks) return;

    currentQuiz.tracks.forEach(track => {
        const btn = document.createElement("button");
        btn.className = "track-btn";
        btn.id = `track-btn-${track.index}`;
        btn.textContent = track.index;
        
        if (track.index === currentTrackIndex) btn.classList.add("active");
        if (playedTracks.has(track.index)) btn.classList.add("played");

        btn.onclick = () => selectTrack(track.index);
        tracksGrid.appendChild(btn);
    });
    updateProgressDisplay();
}

function updateProgressDisplay() {
    if (!currentQuiz) return;
    const total = currentQuiz.total_tracks || currentQuiz.tracks.length;
    gameProgress.textContent = `Сыграно ${playedTracks.size} из ${total}`;
}

// --- Select and Load Track ---
function selectTrack(index) {
    currentTrackIndex = index;
    stopAudio();

    // UI Updates
    document.querySelectorAll(".track-btn").forEach(b => b.classList.remove("active"));
    const activeBtn = document.getElementById(`track-btn-${index}`);
    if (activeBtn) activeBtn.classList.add("active");

    const trackData = currentQuiz.tracks.find(t => t.index === index);
    if (!trackData) return;

    // Show Question View, Hide Answer View
    questionCard.classList.remove("hidden");
    answerCard.classList.add("hidden");

    questionText.textContent = `Трек #${index}: ${trackData.question}`;
    audioPlayer.src = `${API_URL}${trackData.audio_url}`;
    audioPlayer.load();

    // Enable buttons
    playPauseBtn.disabled = false;
    replayBtn.disabled = false;
    revealBtn.disabled = false;

    resetTimer();
}

// --- Audio & Timer Logic ---
function playAudio() {
    audioPlayer.play().then(() => {
        vinylDisc.classList.add("spinning");
        playPauseBtn.textContent = "❚❚";
        startTimer();
    }).catch(err => {
        console.error("Ошибка воспроизведения аудио:", err);
    });
}

function pauseAudio() {
    audioPlayer.pause();
    vinylDisc.classList.remove("spinning");
    playPauseBtn.textContent = "▶";
    clearInterval(timerInterval);
}

function stopAudio() {
    pauseAudio();
    try {
        audioPlayer.currentTime = 0;
    } catch (e) {}
    resetTimer();
}

function resetTimer() {
    clearInterval(timerInterval);
    timerCount.textContent = "20";
    progressBarFill.style.width = "0%";
}

function startTimer() {
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        const current = audioPlayer.currentTime || 0;
        const total = 20; // 20-секундный отрезок

        const remaining = Math.max(0, Math.ceil(total - current));
        timerCount.textContent = remaining;

        const progressPercent = (current / total) * 100;
        progressBarFill.style.width = `${Math.min(progressPercent, 100)}%`;

        if (current >= total || audioPlayer.ended) {
            pauseAudio();
            resetTimer();
        }
    }, 100);
}

// Button Events
playPauseBtn.onclick = () => {
    if (audioPlayer.paused) playAudio();
    else pauseAudio();
};

replayBtn.onclick = () => {
    audioPlayer.currentTime = 0;
    playAudio();
};

// --- Reveal Answer ---
revealBtn.onclick = () => {
    pauseAudio();
    const trackData = currentQuiz.tracks.find(t => t.index === currentTrackIndex);
    if (!trackData) return;

    // Mark as played
    playedTracks.add(currentTrackIndex);
    const activeBtn = document.getElementById(`track-btn-${currentTrackIndex}`);
    if (activeBtn) activeBtn.classList.add("played");
    updateProgressDisplay();

    // Fill Answer Card
    artistPhoto.src = `${API_URL}${trackData.photo_url}`;
    answerText.textContent = trackData.answer;

    questionCard.classList.add("hidden");
    answerCard.classList.remove("hidden");

    // Replay audio in answer mode
    audioPlayer.currentTime = 0;
    audioPlayer.play().catch(() => {});
};

answerReplayBtn.onclick = () => {
    audioPlayer.currentTime = 0;
    audioPlayer.play().catch(() => {});
};

nextTrackBtn.onclick = () => {
    // Find next unplayed track
    let nextIndex = null;
    for (let t of currentQuiz.tracks) {
        if (!playedTracks.has(t.index)) {
            nextIndex = t.index;
            break;
        }
    }

    if (nextIndex) {
        selectTrack(nextIndex);
    } else {
        alert("🎉 Поздравляем! Все треки квиза успешно сыграны!");
        backToLobbyBtn.click();
    }
};

// --- Back to Lobby & Reset ---
backToLobbyBtn.onclick = () => {
    stopAudio();
    gameView.classList.add("hidden");
    lobbyView.classList.remove("hidden");
    loadQuizzes();
};

resetGameBtn.onclick = () => {
    if (confirm("Сбросить статус всех сыгранных треков для текущей игры?")) {
        playedTracks.clear();
        renderTracksGrid();
        selectTrack(1);
    }
};

// --- API Configuration Modal ---
apiConfigBtn.onclick = () => {
    apiUrlInput.value = API_URL;
    apiModal.classList.remove("hidden");
};

closeModalBtn.onclick = () => {
    apiModal.classList.add("hidden");
};

saveApiBtn.onclick = () => {
    let newUrl = apiUrlInput.value.trim().replace(/\/$/, "");
    if (!newUrl) newUrl = "http://localhost:8000";
    API_URL = newUrl;
    localStorage.setItem("quiz_api_url", API_URL);
    apiModal.classList.add("hidden");
    checkApiConnection();
};

// Auto-run on page load
document.addEventListener("DOMContentLoaded", () => {
    checkApiConnection();
});
