// ===== STATE =====
let gameState = {
    timer: 60,
    timerInterval: null,
    currentDocId: null,
    tamperedDocs: {},   // docId -> { fieldId -> newValue }
    charUsed: {},       // docId -> number of chars used
};

// ===== INIT =====
function startGame() {
    document.getElementById('screen-title').classList.remove('active');
    document.getElementById('screen-game').classList.add('active');
    buildDocIcons();
    buildSuspectList();
    startTimer();
    showTutorialHint();
}

function restartGame() {
    gameState = {
        timer: 60,
        timerInterval: null,
        currentDocId: null,
        tamperedDocs: {},
        charUsed: {},
    };
    document.getElementById('screen-result').classList.remove('active');
    document.getElementById('screen-title').classList.add('active');
    document.getElementById('doc-placeholder').classList.remove('hidden');
    document.getElementById('doc-viewer').classList.add('hidden');
    document.getElementById('char-panel').classList.add('hidden');
    updateDocIcons();
}

// ===== TUTORIAL HINT =====
function showTutorialHint() {
    const btn = document.querySelector('.suspect-btn');
    btn.style.animation = 'none';
    btn.style.borderColor = 'var(--amber)';
    btn.style.color = 'var(--amber)';
    setTimeout(() => {
        btn.style.borderColor = '';
        btn.style.color = '';
    }, 3000);
}

// ===== TIMER =====
function startTimer() {
    updateTimerDisplay();
    updateProgress();
    gameState.timerInterval = setInterval(() => {
        gameState.timer--;
        updateTimerDisplay();
        updateProgress();
        if (gameState.timer <= 0) {
            clearInterval(gameState.timerInterval);
            autoConfirm();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const el = document.getElementById('timer-display');
    el.textContent = gameState.timer;
    el.classList.toggle('urgent', gameState.timer <= 10);
    document.getElementById('status-text').textContent =
        gameState.timer > 0 ? 'ハッキング中...' : 'AI送信中...';
}

function updateProgress() {
    const pct = ((60 - gameState.timer) / 60) * 100;
    document.getElementById('progress-bar').style.width = pct + '%';
    document.getElementById('progress-dot').style.left = pct + '%';
}

function autoConfirm() {
    confirmTampering();
}

// ===== SUSPECT POPUP =====
function buildSuspectList() {
    const container = document.getElementById('suspect-list');
    container.innerHTML = GAME_DATA.suspects.map(s => `
        <div class="suspect-card">
            <div class="suspect-name">${s.name}</div>
            <div class="suspect-color">服装：${s.color}</div>
            <div class="suspect-times">
                <span class="time-label">朝</span><span>${s.morning}</span>
                <span class="time-label">昼</span><span>${s.noon}</span>
                <span class="time-label">夜</span><span>${s.night}</span>
            </div>
        </div>
    `).join('');
}

function openSuspects() {
    document.getElementById('suspect-popup').classList.remove('hidden');
}

function closeSuspects(event) {
    if (!event || event.target === document.getElementById('suspect-popup') || event.currentTarget.classList.contains('popup-close')) {
        document.getElementById('suspect-popup').classList.add('hidden');
    }
}

// ===== DOC ICONS =====
function buildDocIcons() {
    const container = document.getElementById('doc-icons');
    container.innerHTML = GAME_DATA.documents.map(doc => `
        <button class="doc-icon-btn" id="docbtn-${doc.id}" onclick="openDocument('${doc.id}')">
            <span class="doc-icon-emoji">${doc.icon}</span>
            <span>${doc.title}</span>
        </button>
    `).join('');
}

function updateDocIcons() {
    GAME_DATA.documents.forEach(doc => {
        const btn = document.getElementById('docbtn-' + doc.id);
        if (!btn) return;
        btn.className = 'doc-icon-btn';
        if (doc.id === gameState.currentDocId) btn.classList.add('active');
        if (gameState.tamperedDocs[doc.id] && Object.keys(gameState.tamperedDocs[doc.id]).length > 0) {
            btn.classList.add('tampered');
        }
    });
}

// ===== DOCUMENT VIEWER =====
function openDocument(docId) {
    gameState.currentDocId = docId;
    const doc = GAME_DATA.documents.find(d => d.id === docId);

    document.getElementById('doc-placeholder').classList.add('hidden');
    document.getElementById('doc-viewer').classList.remove('hidden');
    document.getElementById('doc-title').textContent = doc.title;

    renderDocContent(doc);
    updateCharPanel(doc);
    updateDocIcons();
}

function renderDocContent(doc) {
    const container = document.getElementById('doc-content');
    const tampered = gameState.tamperedDocs[doc.id] || {};
    let html = '<p>';

    doc.content.forEach(part => {
        if (!part.editable) {
            html += `<span class="doc-text">${escapeHtml(part.text)}</span>`;
        } else {
            const currentVal = tampered[part.id] !== undefined ? tampered[part.id] : part.text;
            const isTampered = tampered[part.id] !== undefined && tampered[part.id] !== part.text;
            html += `<span class="doc-editable-wrap">
                <input
                    class="doc-editable${isTampered ? ' tampered' : ''}"
                    type="text"
                    id="field-${part.id}"
                    data-doc="${doc.id}"
                    data-field="${part.id}"
                    data-original="${escapeHtml(part.text)}"
                    data-maxchars="${part.max_chars}"
                    value="${escapeHtml(currentVal)}"
                    size="${Math.max(currentVal.length, 4)}"
                    oninput="onFieldInput(this)"
                />
            </span>`;
        }
    });

    html += '</p>';
    container.innerHTML = html;
}

function onFieldInput(input) {
    const docId = input.dataset.doc;
    const fieldId = input.dataset.field;
    const original = input.dataset.original;
    const maxChars = parseInt(input.dataset.maxchars);
    const doc = GAME_DATA.documents.find(d => d.id === docId);

    // Enforce per-field max chars
    if (input.value.length > maxChars) {
        input.value = input.value.slice(0, maxChars);
    }

    // Save to state
    if (!gameState.tamperedDocs[docId]) gameState.tamperedDocs[docId] = {};

    if (input.value === original) {
        delete gameState.tamperedDocs[docId][fieldId];
    } else {
        gameState.tamperedDocs[docId][fieldId] = input.value;
    }

    // Update tampered styling
    input.classList.toggle('tampered', input.value !== original);
    input.size = Math.max(input.value.length, 4);

    updateCharPanel(doc);
    updateDocIcons();
}

function updateCharPanel(doc) {
    document.getElementById('char-panel').classList.remove('hidden');
    const tampered = gameState.tamperedDocs[doc.id] || {};

    let charsUsed = 0;
    Object.entries(tampered).forEach(([fieldId, newVal]) => {
        const part = doc.content.find(p => p.id === fieldId);
        if (part) {
            charsUsed += Math.abs(newVal.length - part.text.length);
        }
    });

    const remaining = doc.total_char_limit - charsUsed;
    const pct = Math.max(0, (remaining / doc.total_char_limit)) * 100;

    document.getElementById('char-remaining').textContent = Math.max(0, remaining);
    document.getElementById('char-bar').style.height = pct + '%';

    // Color warning
    const charVal = document.getElementById('char-remaining');
    charVal.style.color = remaining <= 5 ? 'var(--red)' : remaining <= 10 ? 'var(--amber)' : 'var(--green)';
}

function resetDocument() {
    if (!gameState.currentDocId) return;
    gameState.tamperedDocs[gameState.currentDocId] = {};
    const doc = GAME_DATA.documents.find(d => d.id === gameState.currentDocId);
    renderDocContent(doc);
    updateCharPanel(doc);
    updateDocIcons();
}

// ===== CONFIRM & ANALYZE =====
function confirmTampering() {
    clearInterval(gameState.timerInterval);

    // Build final document texts
    const docPayload = GAME_DATA.documents.map(doc => {
        const tampered = gameState.tamperedDocs[doc.id] || {};
        let text = '';

        doc.content.forEach(part => {
            if (!part.editable) {
                text += part.text;
            } else {
                text += tampered[part.id] !== undefined ? tampered[part.id] : part.text;
            }
        });

        return { id: doc.id, title: doc.title, text };
    });

    showAILoading();

    fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documents: docPayload })
    })
    .then(r => r.json())
    .then(data => {
        hideAILoading();
        showResult(data);
    })
    .catch(err => {
        hideAILoading();
        showResult({ success: false, error: String(err) });
    });
}

// ===== AI LOADING =====
const loadingMessages = [
    'AIが資料を解析中...',
    '証拠の整合性を確認中...',
    '容疑者データと照合中...',
    '最終判定を生成中...',
];
let loadingMsgIndex = 0;
let loadingInterval = null;

function showAILoading() {
    document.getElementById('ai-loading').classList.remove('hidden');
    loadingMsgIndex = 0;
    document.getElementById('ai-loading-text').textContent = loadingMessages[0];
    loadingInterval = setInterval(() => {
        loadingMsgIndex = (loadingMsgIndex + 1) % loadingMessages.length;
        document.getElementById('ai-loading-text').textContent = loadingMessages[loadingMsgIndex];
    }, 1800);
}

function hideAILoading() {
    clearInterval(loadingInterval);
    document.getElementById('ai-loading').classList.add('hidden');
}

// ===== RESULT SCREEN =====
function showResult(data) {
    document.getElementById('screen-game').classList.remove('active');
    document.getElementById('screen-result').classList.add('active');

    const verdictEl = document.getElementById('result-verdict');
    const analysisEl = document.getElementById('ai-analysis-text');
    const gigoEl = document.getElementById('gigo-message');

    if (!data.success) {
        verdictEl.innerHTML = '<span class="verdict-fail">ERROR: AI接続失敗</span>';
        analysisEl.textContent = data.error || '不明なエラー';
        return;
    }

    if (data.player_cleared) {
        verdictEl.innerHTML = '<span class="verdict-clear">▶ ミッション完了 — 冤罪成立</span>';
        gigoEl.classList.remove('hidden');
    } else {
        verdictEl.innerHTML = '<span class="verdict-fail">▶ ミッション失敗 — 身元特定</span>';
        gigoEl.classList.add('hidden');
    }

    analysisEl.textContent = data.analysis;

    // Animate text reveal
    setTimeout(() => {
        gigoEl.style.opacity = '0';
        gigoEl.style.transition = 'opacity 1s';
        if (!gigoEl.classList.contains('hidden')) {
            setTimeout(() => { gigoEl.style.opacity = '1'; }, 100);
        }
    }, 500);
}

// ===== UTILITIES =====
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}