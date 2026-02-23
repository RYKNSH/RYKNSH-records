/* Cyrus Frontend — SPA Logic */

const API_BASE = '';
let currentApiKey = '';
let selectedMode = 'b2b';
let runCount = 0;
let runHistory = [];

// ====== LP: Tenant Creation ======

async function createTenant() {
  const tenantId = document.getElementById('cta-tenant-id').value.trim();
  const name = document.getElementById('cta-name').value.trim();
  const msgEl = document.getElementById('cta-message');

  if (!tenantId || !name) {
    msgEl.innerHTML = '<div class="message message-error">テナントIDと名前を入力してください</div>';
    return;
  }

  const btn = document.getElementById('cta-submit');
  btn.textContent = '作成中...';
  btn.disabled = true;

  try {
    const resp = await fetch(`${API_BASE}/api/tenants/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tenant_id: tenantId, name, plan: 'free' }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Failed to create tenant');
    }

    const data = await resp.json();
    localStorage.setItem('cyrus_api_key', data.api_key);
    localStorage.setItem('cyrus_tenant_id', data.tenant_id);
    localStorage.setItem('cyrus_tenant_name', data.name);
    localStorage.setItem('cyrus_plan', data.plan);

    msgEl.innerHTML = `
      <div class="message message-success">
        ✅ アカウント作成完了！<br>
        <strong>API Key:</strong> <code style="font-size:0.8rem;">${data.api_key}</code><br>
        <small>このキーは一度しか表示されません。安全な場所に保存してください。</small>
      </div>
    `;
    btn.textContent = 'Dashboard を開く →';
    btn.disabled = false;
    btn.onclick = () => window.location.href = '/static/dashboard.html';
  } catch (e) {
    msgEl.innerHTML = `<div class="message message-error">❌ ${e.message}</div>`;
    btn.textContent = '無料アカウントを作成 →';
    btn.disabled = false;
  }
}

// ====== Dashboard: Auth ======

function login() {
  const key = document.getElementById('login-key').value.trim();
  const msgEl = document.getElementById('login-message');

  if (!key || !key.startsWith('cyrus_')) {
    msgEl.innerHTML = '<div class="message message-error">有効なAPIキーを入力してください</div>';
    return;
  }

  localStorage.setItem('cyrus_api_key', key);
  currentApiKey = key;
  showDashboard();
}

function logout() {
  localStorage.removeItem('cyrus_api_key');
  currentApiKey = '';
  document.getElementById('login-overlay').classList.remove('hidden');
  document.getElementById('dashboard-main').classList.add('hidden');
}

function showDashboard() {
  document.getElementById('login-overlay').classList.add('hidden');
  document.getElementById('dashboard-main').classList.remove('hidden');

  const plan = localStorage.getItem('cyrus_plan') || 'usage';
  const name = localStorage.getItem('cyrus_tenant_name') || '';
  const tenantId = localStorage.getItem('cyrus_tenant_id') || '';

  document.getElementById('nav-status').textContent = '接続中';
  document.getElementById('nav-plan').textContent = plan.toUpperCase();
  document.getElementById('tenant-name').textContent = name;
  document.getElementById('stat-runs').textContent = runCount;
  document.getElementById('settings-tenant-id').textContent = tenantId;
  document.getElementById('settings-plan').textContent = plan;
}

// ====== Dashboard: Tabs ======

function switchTab(tab) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
  document.getElementById(`tab-${tab}`).classList.remove('hidden');
  document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
}

// ====== Dashboard: Pipeline ======

function selectMode(mode) {
  selectedMode = mode;
  document.querySelectorAll('.mode-btn').forEach(el => el.classList.remove('active'));
  document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
}

async function runPipeline() {
  const industry = document.getElementById('run-industry').value.trim() || 'saas';
  const btn = document.getElementById('run-btn');
  const loading = document.getElementById('run-loading');
  const loadingFill = document.getElementById('run-loading-fill');

  btn.disabled = true;
  btn.textContent = '実行中...';
  loading.style.display = 'block';
  loadingFill.style.width = '30%';

  const entityTypes = { b2b: 'organization', b2c: 'individual', c2c: 'creator' };

  const blueprint = {
    business_model: selectedMode,
    entity_config: { type: entityTypes[selectedMode], industry },
    trust_config: { method: selectedMode === 'b2b' ? 'challenger' : '' },
    conversion_config: { mode: selectedMode },
    acquisition_config: { channels: {} },
  };

  try {
    loadingFill.style.width = '60%';

    const resp = await fetch(`${API_BASE}/api/growth/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': currentApiKey,
      },
      body: JSON.stringify({ blueprint }),
    });

    loadingFill.style.width = '90%';

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Pipeline execution failed');
    }

    const data = await resp.json();
    loadingFill.style.width = '100%';

    runCount++;
    document.getElementById('stat-runs').textContent = runCount;
    document.getElementById('stat-last').textContent = new Date().toLocaleTimeString('ja-JP');

    displayResult(data);

    runHistory.unshift({ mode: selectedMode, time: new Date(), data });
    updateResultsTab();

  } catch (e) {
    document.getElementById('run-result').classList.add('visible');
    document.getElementById('result-json').textContent = `Error: ${e.message}`;
  } finally {
    setTimeout(() => {
      loading.style.display = 'none';
      loadingFill.style.width = '0%';
    }, 500);
    btn.disabled = false;
    btn.textContent = '実行 →';
  }
}

function displayResult(data) {
  const panel = document.getElementById('run-result');
  panel.classList.add('visible');

  document.getElementById('result-mode').textContent = data.pipeline_used?.toUpperCase() || selectedMode.toUpperCase();

  // Node metrics
  const metricsEl = document.getElementById('result-metrics');
  const metrics = data.node_metrics || [];
  metricsEl.innerHTML = metrics.map(m => `
    <div class="metric-item">
      <div class="name">${m.node || '—'}</div>
      <div class="time">${m.duration_ms ? m.duration_ms.toFixed(1) + 'ms' : '—'}</div>
    </div>
  `).join('');

  // Performance
  const perf = data.performance_metrics || {};
  document.getElementById('result-performance').textContent = JSON.stringify(perf, null, 2);

  // Full JSON
  document.getElementById('result-json').textContent = JSON.stringify(data, null, 2);
}

function updateResultsTab() {
  const list = document.getElementById('results-list');
  list.innerHTML = runHistory.map((r, i) => `
    <div class="dash-card" style="margin-bottom:1rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <span class="plan-badge">${r.mode.toUpperCase()}</span>
          <span style="color:var(--text-muted);font-size:0.85rem;margin-left:0.5rem;">${r.time.toLocaleString('ja-JP')}</span>
        </div>
        <span style="color:var(--accent);font-family:var(--font-display);font-weight:600;">${(r.data.node_metrics || []).length} nodes</span>
      </div>
    </div>
  `).join('');
}

// ====== Dashboard: API Keys ======

let keyVisible = false;

function toggleKeyVisibility() {
  keyVisible = !keyVisible;
  document.getElementById('current-key-display').textContent = keyVisible ? currentApiKey : '••••••••••••••••••••';
}

function copyKey() {
  navigator.clipboard.writeText(currentApiKey).then(() => {
    const btn = event.target;
    btn.textContent = 'コピー済み!';
    setTimeout(() => btn.textContent = 'コピー', 1500);
  });
}

// ====== Scroll Reveal ======

function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ====== Init ======

document.addEventListener('DOMContentLoaded', () => {
  initReveal();

  // Dashboard auto-login
  const savedKey = localStorage.getItem('cyrus_api_key');
  if (savedKey && window.location.pathname.includes('dashboard')) {
    currentApiKey = savedKey;
    showDashboard();
  }
});
