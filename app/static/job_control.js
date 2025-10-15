// ===============================
// Job Control JS - Fixed & Functional v2
// ===============================

// Elements
const liveTimer = document.getElementById('liveTimer');
const progressBar = document.getElementById('progressBar');
const jobStatusLabel = document.getElementById('jobStatusLabel');
const startButton = document.getElementById('startButton');
const resumeButton = document.getElementById('resumeButton');
const stopButton = document.getElementById('stopButton');
const pauseButton = document.getElementById('pauseButton');
const pauseBox = document.getElementById('pauseReasonBox');
const pauseInput = document.getElementById('pauseReasonInput');
const confirmPauseBtn = document.getElementById('confirmPauseBtn');

// Hidden Inputs
let elapsedSeconds = parseInt(document.getElementById('initialElapsed').value) || 0;
const targetSeconds = parseInt(document.getElementById('targetSeconds').value) || 5400;
let jobStartStr = document.getElementById('jobStartTime').value;
let jobStart = jobStartStr && jobStartStr !== "null" ? new Date(jobStartStr) : null;
let timerInterval = null;

// ===============================
// Format seconds to d:h:m:s
// ===============================
function formatTime(seconds) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    let str = '';
    if (d > 0) str += `${d}d `;
    if (h > 0 || d > 0) str += `${h}h `;
    if (m > 0 || h > 0 || d > 0) str += `${m}m `;
    str += `${s}s`;
    return str;
}

// ===============================
// Update Timer & Progress Bar
// ===============================
function updateTimer() {
    let total = elapsedSeconds;
    if (jobStart) {
        total += Math.floor((Date.now() - jobStart.getTime()) / 1000);
    }
    total = Math.max(0, total);
    liveTimer.innerText = formatTime(total);

    let percent = Math.min(100, (total / targetSeconds) * 100);
    progressBar.style.width = percent + '%';
    progressBar.style.backgroundColor = total > targetSeconds ? 'red' : '#00c8df';
}

// ===============================
// Animate Buttons
// ===============================
function animateButtons(state) {
    startButton.disabled = false;
    resumeButton.disabled = false;
    stopButton.disabled = false;

    if (state === 'running') {
        startButton.disabled = true;
        resumeButton.disabled = true;
    }
    if (state === 'paused') {
        startButton.disabled = true;
        resumeButton.disabled = false;
    }
    if (state === 'stopped') {
        startButton.disabled = true;
        resumeButton.disabled = true;
        stopButton.disabled = true;
    }
}

// ===============================
// AJAX POST with sync
// ===============================
async function postAction(url, data = {}) {
    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (!resp.ok) throw new Error('Network error');
        const json = await resp.json();
        if (json.total_elapsed !== undefined) elapsedSeconds = json.total_elapsed;
        if (json.start_time) jobStart = new Date(json.start_time);
        if (json.status) jobStatusLabel.innerText = json.status;
        updateTimer();
    } catch (err) {
        console.error(err);
        alert('An error occurred. Check console for details.');
    }
}

// ===============================
// Button Actions
// ===============================
function startJob() {
    if (!jobStart) jobStart = new Date();
    animateButtons('running');
    if (!timerInterval) timerInterval = setInterval(updateTimer, 1000);
    postAction(`/start_job/{{ job.id }}`, {elapsed: elapsedSeconds});
}

function pauseJob() {
    if (!pauseInput.value.trim()) return alert("Enter a reason to pause.");
    if (jobStart) elapsedSeconds += Math.floor((Date.now() - jobStart.getTime()) / 1000);
    jobStart = null;
    clearInterval(timerInterval);
    timerInterval = null;
    animateButtons('paused');
    togglePauseBox(false);
    postAction(`/pause_job/{{ job.id }}`, {elapsed: elapsedSeconds, reason: pauseInput.value});
    pauseInput.value = "";
}

function resumeJob() {
    if (!jobStart) jobStart = new Date();
    if (!timerInterval) timerInterval = setInterval(updateTimer, 1000);
    animateButtons('running');
    postAction(`/resume_job/{{ job.id }}`, {elapsed: elapsedSeconds});
}

function stopJob() {
    if (jobStart) elapsedSeconds += Math.floor((Date.now() - jobStart.getTime()) / 1000);
    jobStart = null;
    clearInterval(timerInterval);
    timerInterval = null;
    animateButtons('stopped');
    postAction(`/stop_job/{{ job.id }}`, {elapsed: elapsedSeconds});
    localStorage.removeItem('jobElapsed');
}

// ===============================
// Pause Box Toggle
// ===============================
function togglePauseBox(forceState = null) {
    if (forceState !== null) {
        pauseBox.style.display = forceState ? 'flex' : 'none';
    } else {
        pauseBox.style.display = pauseBox.style.display === 'none' ? 'flex' : 'none';
    }
}

// ===============================
// Current Time Display
// ===============================
const currentTimeSpan = document.getElementById('currentTime');
setInterval(() => currentTimeSpan.innerText = new Date().toLocaleTimeString(), 1000);

// ===============================
// Event Listeners
// ===============================
startButton.addEventListener('click', startJob);
pauseButton.addEventListener('click', () => togglePauseBox());
confirmPauseBtn.addEventListener('click', pauseJob);
resumeButton.addEventListener('click', resumeJob);
stopButton.addEventListener('click', stopJob);

// ===============================
// Auto-start Timer if Job Running
// ===============================
if (["Running", "In Progress"].includes(jobStatusLabel.innerText)) {
    if (!timerInterval) timerInterval = setInterval(updateTimer, 1000);
    animateButtons('running');
}

// Initial update
updateTimer();
