const API_BASE = '/admin/api';

let models = {};
let apiKeys = [];

document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    loadData();
    initializeModals();
});

function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

async function loadData() {
    try {
        await Promise.all([
            loadModels(),
            loadApiKeys()
        ]);
    } catch (error) {
        showAlert('Failed to load data: ' + error.message, 'error');
    }
}

async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/models`);
        const data = await response.json();
        if (data.success) {
            models = data.data;
            renderModels();
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        throw error;
    }
}

async function loadApiKeys() {
    try {
        const response = await fetch(`${API_BASE}/api-keys`);
        const data = await response.json();
        if (data.success) {
            apiKeys = data.data;
            renderApiKeys();
        }
    } catch (error) {
        console.error('Failed to load API keys:', error);
        throw error;
    }
}

function renderModels() {
    const container = document.getElementById('model-list');
    if (!container) return;
    
    if (Object.keys(models).length === 0) {
        container.innerHTML = '<div class="loading">No models configured</div>';
        return;
    }
    
    container.innerHTML = Object.entries(models).map(([name, config]) => `
        <div class="model-item">
            <div class="model-item-header">
                <span class="model-name">${escapeHtml(name)}</span>
                <div class="item-actions">
                    <button class="btn btn-primary btn-sm" onclick="openEditModelModal('${escapeHtml(name)}')">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteModel('${escapeHtml(name)}')">Delete</button>
                </div>
            </div>
            <div class="model-details">
                <p><strong>Base URL:</strong> ${escapeHtml(config.base_url)}</p>
                <p><strong>Target Model:</strong> ${escapeHtml(config.target_model)}</p>
                <p><strong>Max Tokens:</strong> ${config.max_tokens}</p>
                <p><strong>Stream:</strong> ${config.supports_stream ? 'Yes' : 'No'}</p>
                <p><strong>Timeout:</strong> ${config.timeout}s</p>
            </div>
        </div>
    `).join('');
}

function renderApiKeys() {
    const container = document.getElementById('api-key-list');
    if (!container) return;
    
    if (apiKeys.length === 0) {
        container.innerHTML = '<div class="loading">No API keys configured</div>';
        return;
    }
    
    container.innerHTML = apiKeys.map(key => `
        <div class="api-key-item">
            <div class="api-key-item-header">
                <span class="api-key-name">API Key</span>
                <div class="item-actions">
                    <button class="btn btn-danger btn-sm" onclick="deleteApiKey('${escapeHtml(key)}')">Delete</button>
                </div>
            </div>
            <div class="api-key-value">${escapeHtml(key)}</div>
        </div>
    `).join('');
}

function initializeModals() {
    const closeBtns = document.querySelectorAll('.close-btn');
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal').classList.remove('active');
        });
    });
    
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('active');
        }
    });
}

function openAddModelModal() {
    document.getElementById('model-form').reset();
    document.getElementById('model-modal-title').textContent = 'Add Model';
    document.getElementById('model-name').disabled = false;
    document.getElementById('model-modal').classList.add('active');
    document.getElementById('editing-model-name').value = '';
}

function openEditModelModal(modelName) {
    const model = models[modelName];
    if (!model) return;
    
    document.getElementById('model-modal-title').textContent = 'Edit Model';
    document.getElementById('model-name').value = modelName;
    document.getElementById('model-name').disabled = true;
    document.getElementById('base-url').value = model.base_url;
    document.getElementById('auth-header').value = model.auth_header;
    document.getElementById('target-model').value = model.target_model;
    document.getElementById('max-tokens').value = model.max_tokens;
    document.getElementById('supports-stream').checked = model.supports_stream;
    document.getElementById('timeout').value = model.timeout;
    document.getElementById('editing-model-name').value = modelName;
    document.getElementById('model-modal').classList.add('active');
}

async function saveModel() {
    const editingName = document.getElementById('editing-model-name').value;
    const modelName = document.getElementById('model-name').value;
    const baseUrl = document.getElementById('base-url').value;
    const authHeader = document.getElementById('auth-header').value;
    const targetModel = document.getElementById('target-model').value;
    const maxTokens = parseInt(document.getElementById('max-tokens').value);
    const supportsStream = document.getElementById('supports-stream').checked;
    const timeout = parseInt(document.getElementById('timeout').value);
    
    if (!modelName || !baseUrl || !targetModel || !maxTokens) {
        showAlert('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/models/${encodeURIComponent(modelName)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_url: baseUrl,
                auth_header: authHeader,
                target_model: targetModel,
                max_tokens: maxTokens,
                supports_stream: supportsStream,
                timeout: timeout
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showAlert(data.message, 'success');
            document.getElementById('model-modal').classList.remove('active');
            await loadModels();
        } else {
            showAlert(data.detail || 'Failed to save model', 'error');
        }
    } catch (error) {
        showAlert('Failed to save model: ' + error.message, 'error');
    }
}

async function deleteModel(modelName) {
    if (!confirm(`Are you sure you want to delete model "${modelName}"?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/models/${encodeURIComponent(modelName)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.success) {
            showAlert(data.message, 'success');
            await loadModels();
        } else {
            showAlert(data.detail || 'Failed to delete model', 'error');
        }
    } catch (error) {
        showAlert('Failed to delete model: ' + error.message, 'error');
    }
}

function openAddApiKeyModal() {
    document.getElementById('api-key-form').reset();
    document.getElementById('api-key-modal').classList.add('active');
}

async function addApiKey() {
    const apiKey = document.getElementById('new-api-key').value.trim();
    
    if (!apiKey) {
        showAlert('Please enter an API key', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api-keys?api_key=${encodeURIComponent(apiKey)}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.success) {
            showAlert(data.message, 'success');
            document.getElementById('api-key-modal').classList.remove('active');
            await loadApiKeys();
        } else {
            showAlert(data.detail || 'Failed to add API key', 'error');
        }
    } catch (error) {
        showAlert('Failed to add API key: ' + error.message, 'error');
    }
}

async function deleteApiKey(apiKey) {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api-keys/${encodeURIComponent(apiKey)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.success) {
            showAlert(data.message, 'success');
            await loadApiKeys();
        } else {
            showAlert(data.detail || 'Failed to delete API key', 'error');
        }
    } catch (error) {
        showAlert('Failed to delete API key: ' + error.message, 'error');
    }
}

function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    if (!alert) return;
    
    alert.textContent = message;
    alert.className = `alert alert-${type} active`;
    
    setTimeout(() => {
        alert.classList.remove('active');
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
