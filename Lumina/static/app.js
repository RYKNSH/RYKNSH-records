/* Lumina Dashboard — app.js */

const API_BASE = window.location.origin;
const gallery = [];

// =====================
// Tab Navigation
// =====================
document.querySelectorAll('.header__link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = link.dataset.tab;
        document.querySelectorAll('.header__link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        link.classList.add('active');
        document.getElementById(`tab-${tab}`).classList.add('active');

        // Lazy load data
        if (tab === 'models') loadModels();
        if (tab === 'packs') loadPacks();
        if (tab === 'status') loadSystem();
    });
});

// =====================
// Generate
// =====================
async function generateAsset() {
    const btn = document.getElementById('generateBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');

    const brief = document.getElementById('brief').value.trim();
    if (!brief) { alert('ブリーフを入力してください'); return; }

    btn.disabled = true;
    btnText.hidden = true;
    btnLoader.hidden = false;

    try {
        const body = {
            brief,
            quality_tier: document.getElementById('qualityTier').value,
            tenant_id: document.getElementById('tenantId').value,
        };

        const packId = document.getElementById('stylePack').value;
        if (packId) body.style_pack_id = packId;

        const res = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        const data = await res.json();
        showResult(data, brief);
        gallery.unshift({ ...data, brief, timestamp: new Date().toISOString() });
        updateGallery();

    } catch (err) {
        showResult({ status: 'error', error: err.message }, brief);
    } finally {
        btn.disabled = false;
        btnText.hidden = false;
        btnLoader.hidden = true;
    }
}

function showResult(data, brief) {
    document.getElementById('previewPlaceholder').hidden = true;
    const result = document.getElementById('previewResult');
    result.hidden = false;

    const imageDiv = document.getElementById('resultImage');
    if (data.asset_url && !data.asset_url.includes('example.com')) {
        imageDiv.innerHTML = `<img src="${data.asset_url}" alt="${brief}">`;
    } else {
        imageDiv.innerHTML = `<span style="font-size: 3rem; opacity: 0.2">◈</span>`;
    }

    document.getElementById('resultStatus').textContent = data.status || '—';
    document.getElementById('resultModel').textContent = data.model_used || '—';
    document.getElementById('resultScore').textContent = data.taste_score != null ? `${data.taste_score}/100` : '—';
    document.getElementById('resultId').textContent = data.request_id ? data.request_id.slice(0, 12) + '...' : '—';

    const statusEl = document.getElementById('resultStatus');
    statusEl.style.color = data.status === 'completed' ? 'var(--success)' :
                            data.status === 'failed' ? 'var(--error)' : 'var(--warning)';
}

// =====================
// Gallery
// =====================
function updateGallery() {
    const grid = document.getElementById('galleryGrid');
    if (gallery.length === 0) {
        grid.innerHTML = '<div class="gallery-empty">まだ作品がありません。Generateタブから生成してください。</div>';
        return;
    }

    grid.innerHTML = gallery.map(item => `
        <div class="gallery-item">
            <div class="gallery-item__image">◈</div>
            <div class="gallery-item__info">
                <strong>${item.brief ? item.brief.slice(0, 40) + '...' : 'Untitled'}</strong>
                ${item.quality_tier || 'standard'} · ${item.model_used || 'unknown'} · ${item.taste_score != null ? item.taste_score + '/100' : '—'}
            </div>
        </div>
    `).join('');
}

// =====================
// Models
// =====================
async function loadModels() {
    try {
        const res = await fetch(`${API_BASE}/models`);
        const data = await res.json();
        const grid = document.getElementById('modelsGrid');

        grid.innerHTML = data.models.map(m => `
            <div class="model-card">
                <h4>${m.name}</h4>
                <div class="provider">${m.provider}</div>
                <div class="stat-row"><span>Capability</span><span>${m.capability_score}/100</span></div>
                <div class="stat-row"><span>Cost</span><span>$${m.cost_per_call}</span></div>
            </div>
        `).join('');
    } catch (err) {
        document.getElementById('modelsGrid').innerHTML = `<p style="color: var(--error)">Failed to load models: ${err.message}</p>`;
    }
}

// =====================
// Style Packs
// =====================
async function loadPacks() {
    try {
        const res = await fetch(`${API_BASE}/marketplace/packs`);
        const data = await res.json();
        const grid = document.getElementById('packsGrid');

        grid.innerHTML = data.packs.map(p => `
            <div class="pack-card">
                <h4>${p.name}</h4>
                <div class="genre">${p.genre}</div>
                <div class="stat-row"><span>Price</span><span>¥${p.price}</span></div>
                <div class="stat-row"><span>Downloads</span><span>${p.downloads}</span></div>
                <div class="stat-row"><span>Taste Score</span><span>${p.taste_score}/100</span></div>
            </div>
        `).join('');

        // Update Style Pack select
        const select = document.getElementById('stylePack');
        select.innerHTML = '<option value="">None</option>' +
            data.packs.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    } catch (err) {
        document.getElementById('packsGrid').innerHTML = `<p style="color: var(--error)">Failed to load packs: ${err.message}</p>`;
    }
}

// =====================
// System Status
// =====================
async function loadSystem() {
    // Config
    try {
        const res = await fetch(`${API_BASE}/config/status`);
        const data = await res.json();

        const connections = [
            ['Supabase', data.supabase],
            ['Ada API', data.ada_api],
            ['OpenAI', data.openai],
            ['Stability AI', data.stability_ai],
            ['Black Forest Labs', data.black_forest_labs],
        ];

        document.getElementById('configBody').innerHTML = connections.map(([name, active]) => `
            <div class="conn-row">
                <span>${name}</span>
                <span class="conn-status ${active ? 'on' : 'off'}">${active ? '● Connected' : '○ Disconnected'}</span>
            </div>
        `).join('') + `
            <div class="conn-row" style="margin-top: 0.5rem; border: none;">
                <span>Mode</span>
                <span class="conn-status ${data.use_real_api ? 'on' : 'off'}">${data.use_real_api ? 'Production' : 'Stub'}</span>
            </div>
        `;

        // Update header status
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        if (data.use_real_api) {
            statusDot.classList.add('live');
            statusText.textContent = 'Live';
        } else {
            statusDot.classList.remove('live');
            statusText.textContent = 'Stub Mode';
        }
    } catch (err) {
        document.getElementById('configBody').innerHTML = `<p style="color: var(--error)">${err.message}</p>`;
    }

    // Graph
    try {
        const res = await fetch(`${API_BASE}/graph/spec`);
        const data = await res.json();

        const layerColors = { creation: 'creation', quality: 'quality', delivery: 'delivery' };

        let html = '';
        for (const [layer, nodes] of Object.entries(data.layers || {})) {
            html += `
                <div class="graph-layer">
                    <div class="graph-layer-name ${layerColors[layer] || ''}">${layer}</div>
                    ${nodes.map(n => `<span class="graph-node">${n}</span>`).join(' → ')}
                </div>
            `;
        }

        document.getElementById('graphBody').innerHTML = html || 'No graph spec available';
    } catch (err) {
        document.getElementById('graphBody').innerHTML = `<p style="color: var(--error)">${err.message}</p>`;
    }
}

// =====================
// Init
// =====================
(async function init() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        if (data.api_mode === 'real') {
            statusDot.classList.add('live');
            statusText.textContent = 'Live';
        } else {
            statusText.textContent = `Stub · ${data.providers?.join(', ') || 'none'}`;
        }
    } catch {
        document.querySelector('.status-text').textContent = 'Offline';
    }
})();
