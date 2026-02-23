/* Lumina SaaS Dashboard — Logic */

const API = window.location.origin;
const SESSION_KEY = 'lumina_session';
const HISTORY_KEY = 'lumina_history';

// =====================
// Auth
// =====================
let isLogin = true;

function toggleAuth() {
    isLogin = !isLogin;
    document.getElementById('authTitle').textContent = isLogin ? 'ログイン' : '新規登録';
    document.getElementById('authBtn').textContent = isLogin ? 'ログイン' : 'アカウント作成';
    document.getElementById('authSwitchText').textContent = isLogin ? 'アカウントがない？' : 'すでにアカウントがある？';
    document.getElementById('authSwitchLink').textContent = isLogin ? '新規登録' : 'ログイン';
}

function handleAuth(e) {
    e.preventDefault();
    const email = document.getElementById('authEmail').value;
    const session = {
        email,
        apiKey: 'lum_' + crypto.randomUUID().replace(/-/g, '').slice(0, 24),
        plan: 'standard',
        createdAt: new Date().toISOString(),
    };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    showDashboard(session);
}

function handleLogout() {
    localStorage.removeItem(SESSION_KEY);
    location.reload();
}

function showDashboard(session) {
    const overlay = document.getElementById('authOverlay');
    overlay.hidden = true;
    overlay.style.display = 'none';
    const appEl = document.getElementById('app');
    appEl.hidden = false;
    appEl.style.display = 'flex';
    document.getElementById('userEmail').textContent = session.email;
    document.querySelector('.avatar').textContent = session.email[0].toUpperCase();
    loadApiKeys(session);
    loadHistory();
}

// Auto login
(function initAuth() {
    const s = localStorage.getItem(SESSION_KEY);
    if (s) showDashboard(JSON.parse(s));
})();

// =====================
// Page Navigation
// =====================
function switchPage(name) {
    document.querySelectorAll('.sidebar__link').forEach(l => l.classList.remove('active'));
    document.querySelector(`[data-page="${name}"]`).classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${name}`).classList.add('active');
}

// =====================
// Generate
// =====================
async function dashGenerate() {
    const btn = document.getElementById('dashGenBtn');
    const genText = btn.querySelector('.gen-text');
    const genLoading = btn.querySelector('.gen-loading');
    const brief = document.getElementById('dashBrief').value.trim();
    if (!brief) return;

    btn.disabled = true;
    genText.hidden = true;
    genLoading.hidden = false;

    try {
        const body = {
            brief,
            quality_tier: document.getElementById('dashTier').value,
            tenant_id: 'dashboard-user',
        };
        const packId = document.getElementById('dashPack').value;
        if (packId) body.style_pack_id = packId;

        const res = await fetch(`${API}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const errText = await res.text();
            showDashResult({ status: 'failed', error: `Server Error ${res.status}: ${errText.slice(0, 120)}` }, brief);
            return;
        }
        const data = await res.json();
        showDashResult(data, brief);
        saveToHistory(data, brief);
    } catch (err) {
        showDashResult({ status: 'error', error: err.message }, brief);
    } finally {
        btn.disabled = false;
        genText.hidden = false;
        genLoading.hidden = true;
    }
}

function showDashResult(data, brief) {
    const card = document.getElementById('dashResult');
    const statusColor = data.status === 'completed' ? 'var(--success)' :
        data.status === 'failed' ? 'var(--error)' : 'var(--warning)';

    card.innerHTML = `
        <div class="result-filled">
            <div class="result-filled__image">◈</div>
            <div class="result-meta">
                <div class="result-meta__row">
                    <span class="result-meta__label">Status</span>
                    <span class="result-meta__value" style="color:${statusColor}">${data.status || '—'}</span>
                </div>
                <div class="result-meta__row">
                    <span class="result-meta__label">Model</span>
                    <span class="result-meta__value">${data.model_used || '—'}</span>
                </div>
                <div class="result-meta__row">
                    <span class="result-meta__label">Taste Score</span>
                    <span class="result-meta__value">${data.taste_score != null ? data.taste_score + '/100' : '—'}</span>
                </div>
                <div class="result-meta__row">
                    <span class="result-meta__label">Tier</span>
                    <span class="result-meta__value">${data.quality_tier || '—'}</span>
                </div>
                <div class="result-meta__row">
                    <span class="result-meta__label">Request ID</span>
                    <span class="result-meta__value mono">${data.request_id ? data.request_id.slice(0, 16) + '...' : '—'}</span>
                </div>
                ${data.error ? `<div class="result-meta__row"><span class="result-meta__label">Error</span><span class="result-meta__value" style="color:var(--error)">${data.error}</span></div>` : ''}
            </div>
        </div>
    `;
}

// =====================
// History
// =====================
function saveToHistory(data, brief) {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    history.unshift({ ...data, brief, timestamp: new Date().toISOString() });
    if (history.length > 50) history.pop();
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderHistory(history);
}

function loadHistory() {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
    renderHistory(history);
}

function renderHistory(history) {
    const grid = document.getElementById('historyGrid');
    if (!history.length) {
        grid.innerHTML = '<div class="empty-state">まだ生成履歴がありません</div>';
        return;
    }
    grid.innerHTML = history.map(item => `
        <div class="history-item">
            <div class="history-item__img">◈</div>
            <div class="history-item__info">
                <div class="history-item__brief">${(item.brief || '').slice(0, 50)}${(item.brief || '').length > 50 ? '...' : ''}</div>
                <div class="history-item__meta">
                    ${item.quality_tier || 'standard'} · ${item.model_used || '—'} · ${item.taste_score != null ? item.taste_score + '/100' : '—'} · ${new Date(item.timestamp).toLocaleString('ja-JP')}
                </div>
            </div>
        </div>
    `).join('');
}

// =====================
// API Keys
// =====================
function loadApiKeys(session) {
    const keys = JSON.parse(localStorage.getItem('lumina_api_keys') || '[]');
    if (!keys.length) {
        keys.push({ name: 'Default Key', key: session.apiKey, created: session.createdAt });
        localStorage.setItem('lumina_api_keys', JSON.stringify(keys));
    }
    renderApiKeys(keys);
}

function createApiKey() {
    const keys = JSON.parse(localStorage.getItem('lumina_api_keys') || '[]');
    const name = prompt('キー名を入力:') || `Key ${keys.length + 1}`;
    keys.push({
        name,
        key: 'lum_' + crypto.randomUUID().replace(/-/g, '').slice(0, 24),
        created: new Date().toISOString(),
    });
    localStorage.setItem('lumina_api_keys', JSON.stringify(keys));
    renderApiKeys(keys);
}

function deleteApiKey(index) {
    const keys = JSON.parse(localStorage.getItem('lumina_api_keys') || '[]');
    keys.splice(index, 1);
    localStorage.setItem('lumina_api_keys', JSON.stringify(keys));
    renderApiKeys(keys);
}

function renderApiKeys(keys) {
    const list = document.getElementById('apiKeysList');
    list.innerHTML = keys.map((k, i) => `
        <div class="api-key-row">
            <div class="api-key-row__name">${k.name}</div>
            <div class="api-key-row__key">${k.key.slice(0, 8)}${'•'.repeat(16)}${k.key.slice(-4)}</div>
            <div class="api-key-row__date">${new Date(k.created).toLocaleDateString('ja-JP')}</div>
            <button class="api-key-row__delete" onclick="deleteApiKey(${i})">削除</button>
        </div>
    `).join('');
}
