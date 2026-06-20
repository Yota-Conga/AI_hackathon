// ===== STATE =====
let gameState = {
    timer: 60,
    timerInterval: null,
    currentDocId: null,
    tamperedDocs: {},
    modelAnswer: null,
    modelAnswerVisible: false,
};

// ===== INIT =====
function startGame() {
    try {
        gameState = { timer: 120, totalTime: 120, timerInterval: null, currentDocId: null, tamperedDocs: {}, modelAnswer: null, modelAnswerVisible: false };
        // 画面切り替え
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById('screen-game').classList.add('active');
        // 初期表示リセット
        document.getElementById('doc-placeholder').classList.remove('hidden');
        document.getElementById('doc-viewer').classList.add('hidden');
        document.getElementById('char-panel').classList.add('hidden');
        buildDocIcons();
        buildSuspectMatrix();
        startTimer();
        showTutorialHint();
    } catch(e) {
        console.error('startGame error:', e);
        alert('初期化エラー: ' + e.message);
    }
}

function restartGame() {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('screen-title').classList.add('active');
}

// ===== TUTORIAL HINT =====
function showTutorialHint() {
    const btn = document.querySelector('.suspect-btn');
    if (!btn) return;
    btn.style.borderColor = 'var(--amber)';
    btn.style.color = 'var(--amber)';
    setTimeout(() => { btn.style.borderColor = ''; btn.style.color = ''; }, 3000);
}

// ===== TIMER =====
function startTimer() {
    updateTimerDisplay();
    updateProgress();
    gameState.timerInterval = setInterval(() => {
        gameState.timer--;
        updateTimerDisplay();
        updateProgress();
        if (gameState.timer <= 0) { clearInterval(gameState.timerInterval); autoConfirm(); }
    }, 1000);
}

function updateTimerDisplay() {
    const el = document.getElementById('timer-display');
    el.textContent = gameState.timer;
    el.classList.toggle('urgent', gameState.timer <= 10);
    document.getElementById('status-text').textContent = gameState.timer > 0 ? 'ハッキング中...' : 'AI送信中...';
}

function updateProgress() {
    const total = gameState.totalTime;
    const pct = Math.min(100, Math.max(0, ((total - gameState.timer) / total) * 100));
    document.getElementById('progress-bar').style.width = pct + '%';
    document.getElementById('progress-dot').style.left = pct + '%';
}

function autoConfirm() { confirmTampering(); }

// ===== SUSPECT MATRIX (4 suspects x 3 time slots) =====
function buildSuspectMatrix() {
    const container = document.getElementById('suspect-list');
    const suspects = GAME_DATA.suspects;
    let html = `<table class="suspect-matrix">
        <thead>
            <tr>
                <th>容疑者</th>
                <th>朝</th>
                <th>昼</th>
                <th>夜</th>
            </tr>
        </thead>
        <tbody>`;
    suspects.forEach(s => {
        const isPlayer = s.is_player === true;
        const rowClass = isPlayer ? ' class="player-row"' : '';
        const nameBadge = isPlayer ? ' <span class="you-badge">YOU</span>' : '';
        html += `<tr${rowClass}>
            <th>${s.name}${nameBadge}<span class="suspect-color-tag">${s.color}</span></th>
            <td>${s.morning}</td>
            <td>${s.noon}</td>
            <td>${s.night}</td>
        </tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

function openSuspects() { document.getElementById('suspect-popup').classList.remove('hidden'); }
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
        if (gameState.tamperedDocs[doc.id] && Object.keys(gameState.tamperedDocs[doc.id]).length > 0) btn.classList.add('tampered');
    });
}

// ===== DOCUMENT VIEWER =====
function openDocument(docId) {
    gameState.currentDocId = docId;
    const doc = GAME_DATA.documents.find(d => d.id === docId);
    document.getElementById('doc-placeholder').classList.add('hidden');
    document.getElementById('doc-viewer').classList.remove('hidden');

    // Paper metadata
    document.getElementById('paper-docnum').textContent = '文書番号：' + doc.doc_number;
    document.getElementById('paper-date').textContent = doc.date;
    document.getElementById('paper-title').textContent = doc.title;
    document.getElementById('paper-author').textContent = '作成者：' + doc.author;

    renderDocContent(doc);
    updateCharPanel(doc);
    updateDocIcons();
}

function renderDocContent(doc) {
    const container = document.getElementById('doc-content');
    const tampered = gameState.tamperedDocs[doc.id] || {};

    // Group parts into paragraphs by section headings (【...】)
    let html = '<p>';
    let firstPart = true;

    doc.content.forEach((part, idx) => {
        if (!part.editable) {
            // Start new paragraph at 【 if not the first part
            if (!firstPart && part.text.startsWith('【')) {
                html += '</p><p>';
            }
            html += `<span class="doc-text">${escapeHtml(part.text)}</span>`;
        } else {
            const currentVal = tampered[part.id] !== undefined ? tampered[part.id] : part.text;
            const isTampered = tampered[part.id] !== undefined && tampered[part.id] !== part.text;
            // Use a span-sized input that grows with content
            html += `<span class="doc-editable-wrap"><input
                class="doc-editable${isTampered ? ' tampered' : ''}"
                type="text"
                id="field-${part.id}"
                data-doc="${doc.id}"
                data-field="${part.id}"
                data-original="${escapeHtml(part.text)}"
                data-maxchars="${part.max_chars}"
                value="${escapeHtml(currentVal)}"
                style="width:${Math.max(currentVal.length, 4) * 1.05}em"
                oninput="onFieldInput(this)"
            /></span>`;
        }
        firstPart = false;
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

    if (input.value.length > maxChars) input.value = input.value.slice(0, maxChars);

    if (!gameState.tamperedDocs[docId]) gameState.tamperedDocs[docId] = {};
    if (input.value === original) { delete gameState.tamperedDocs[docId][fieldId]; }
    else { gameState.tamperedDocs[docId][fieldId] = input.value; }

    input.classList.toggle('tampered', input.value !== original);
    // Dynamically resize
    input.style.width = Math.max(input.value.length, 4) * 1.05 + 'em';

    updateCharPanel(doc);
    updateDocIcons();
}

function updateCharPanel(doc) {
    document.getElementById('char-panel').classList.remove('hidden');
    const tampered = gameState.tamperedDocs[doc.id] || {};
    let charsUsed = 0;
    Object.entries(tampered).forEach(([fieldId, newVal]) => {
        const part = doc.content.find(p => p.id === fieldId);
        if (part) charsUsed += Math.abs(newVal.length - part.text.length);
    });
    const remaining = doc.total_char_limit - charsUsed;
    const pct = Math.max(0, (remaining / doc.total_char_limit)) * 100;
    document.getElementById('char-remaining').textContent = Math.max(0, remaining);
    document.getElementById('char-bar').style.height = pct + '%';
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
    const docPayload = GAME_DATA.documents.map(doc => {
        const tampered = gameState.tamperedDocs[doc.id] || {};
        let text = '';
        doc.content.forEach(part => {
            text += (!part.editable) ? part.text : (tampered[part.id] !== undefined ? tampered[part.id] : part.text);
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
    .then(data => { hideAILoading(); showResult(data); })
    .catch(err => { hideAILoading(); showResult({ success: false, error: String(err) }); });
}

// ===== AI LOADING =====
const loadingMessages = ['AIが資料を解析中...','証拠の整合性を確認中...','容疑者データと照合中...','最終判定を生成中...'];
let loadingMsgIndex = 0, loadingInterval = null;

function showAILoading() {
    document.getElementById('ai-loading').classList.remove('hidden');
    loadingMsgIndex = 0;
    document.getElementById('ai-loading-text').textContent = loadingMessages[0];
    loadingInterval = setInterval(() => {
        loadingMsgIndex = (loadingMsgIndex + 1) % loadingMessages.length;
        document.getElementById('ai-loading-text').textContent = loadingMessages[loadingMsgIndex];
    }, 1800);
}
function hideAILoading() { clearInterval(loadingInterval); document.getElementById('ai-loading').classList.add('hidden'); }

// ===== RESULT SCREEN =====
function showResult(data) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('screen-result').classList.add('active');

    const verdictEl = document.getElementById('result-verdict');
    const analysisEl = document.getElementById('ai-analysis-text');
    const gigoEl = document.getElementById('gigo-message');
    const maBox = document.getElementById('model-answer-box');

    if (!data.success) {
        verdictEl.innerHTML = '<span class="verdict-fail">ERROR: AI接続失敗</span>';
        analysisEl.textContent = data.error || '不明なエラー';
        return;
    }

    if (data.player_cleared) {
        verdictEl.innerHTML = '<span class="verdict-clear">▶ ミッション完了 ── 冤罪成立</span>';
        gigoEl.classList.remove('hidden');
    } else {
        verdictEl.innerHTML = '<span class="verdict-fail">▶ ミッション失敗 ── 身元特定</span>';
        gigoEl.classList.add('hidden');
    }

    analysisEl.innerHTML = renderMarkdown(data.analysis);

    // Store model answer
    if (data.model_answer) {
        gameState.modelAnswer = data.model_answer;
        buildModelAnswer(data.model_answer);
        maBox.classList.add('hidden'); // hidden until button clicked
        gameState.modelAnswerVisible = false;
    }
}

function buildModelAnswer(ma) {
    const el = document.getElementById('model-answer-content');
    let html = `<div class="ma-target">🎯 狙うべき犯人：<strong>${ma.target}</strong></div>`;
    html += `<div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--text-muted);margin-bottom:0.5rem;letter-spacing:0.1em;">推奨する改竄箇所</div>`;
    ma.steps.forEach((step, i) => {
        html += `<div class="ma-step">
            <div class="ma-step-doc">📄 ${step.doc} ／ ${step.field}</div>
            <div class="ma-step-change"><span class="from">「${step.from}」</span> → <span class="to">「${step.to}」</span></div>
            <div class="ma-step-reason">${step.reason}</div>
        </div>`;
    });
    html += `<div class="ma-summary">💡 ${ma.summary}</div>`;
    el.innerHTML = html;
}

function toggleModelAnswer() {
    const maBox = document.getElementById('model-answer-box');
    const btn = document.querySelector('.result-btns .btn-start:first-child');
    gameState.modelAnswerVisible = !gameState.modelAnswerVisible;
    if (gameState.modelAnswerVisible) {
        maBox.classList.remove('hidden');
        btn.querySelector('span.btn-text') ? btn.querySelector('span.btn-text').textContent = '模範解答を隠す' : btn.childNodes[0].textContent = '模範解答を隠す';
    } else {
        maBox.classList.add('hidden');
        btn.childNodes[0].textContent = '模範解答を見る';
    }
}

// ===== UTILITIES =====
function renderMarkdown(text) {
    // Escape HTML first
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    // ## Heading
    html = html.replace(/^## (.+)$/gm, '<h3 class="ai-heading">$1</h3>');
    // **bold**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // *italic*
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // newlines to <br>
    html = html.replace(/
/g, '<br>');
    return html;
}

function escapeHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}