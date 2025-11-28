// Settings page script
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  setupEventListeners();
});

// Load saved settings
function loadSettings() {
  chrome.storage.local.get([
    'useCustomLLM',
    'apiKey',
    'modelName',
    'temperature',
    'maxTokens'
  ], (result) => {
    // Toggle custom LLM
    const useCustom = result.useCustomLLM || false;
    const toggle = document.getElementById('use-custom-llm');
    const llmSettings = document.getElementById('llm-settings');
    
    if (useCustom) {
      toggle.classList.add('active');
      llmSettings.style.display = 'block';
    }

    // Load values
    if (result.apiKey) {
      document.getElementById('api-key').value = result.apiKey;
    }
    if (result.modelName) {
      document.getElementById('model-name').value = result.modelName;
    }
    if (result.temperature !== undefined) {
      document.getElementById('temperature').value = result.temperature;
      document.getElementById('temp-value').textContent = result.temperature;
    }
    if (result.maxTokens) {
      document.getElementById('max-tokens').value = result.maxTokens;
    }
  });
}

// Setup event listeners
function setupEventListeners() {
  // Toggle custom LLM settings
  document.getElementById('use-custom-llm').addEventListener('click', function() {
    this.classList.toggle('active');
    const llmSettings = document.getElementById('llm-settings');
    llmSettings.style.display = this.classList.contains('active') ? 'block' : 'none';
  });

  // Temperature slider
  document.getElementById('temperature').addEventListener('input', function() {
    document.getElementById('temp-value').textContent = this.value;
  });

  // Save button
  document.getElementById('save-btn').addEventListener('click', saveSettings);

  // Reset button
  document.getElementById('reset-btn').addEventListener('click', resetSettings);

  // Test Connection button
  document.getElementById('test-connection').addEventListener('click', testConnection);
}

// Save settings
function saveSettings() {
  const useCustomLLM = document.getElementById('use-custom-llm').classList.contains('active');
  const apiKey = document.getElementById('api-key').value.trim();
  const modelName = document.getElementById('model-name').value;
  const temperature = parseFloat(document.getElementById('temperature').value);
  const maxTokens = parseInt(document.getElementById('max-tokens').value) || null;

  // Validate if custom LLM is enabled
  if (useCustomLLM) {
    if (!apiKey) {
      showAlert('Please enter an API key', 'error');
      return;
    }
    if (maxTokens && (maxTokens < 100 || maxTokens > 8192)) {
      showAlert('Max tokens must be between 100 and 8192', 'error');
      return;
    }
  }

  // Save to chrome.storage
  chrome.storage.local.set({
    useCustomLLM: useCustomLLM,
    apiKey: useCustomLLM ? apiKey : '',
    modelName: useCustomLLM ? modelName : '',
    temperature: useCustomLLM ? temperature : null,
    maxTokens: useCustomLLM ? maxTokens : null
  }, () => {
    showAlert('Settings saved successfully!', 'success');
    
    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      document.getElementById('alert').style.display = 'none';
    }, 3000);
  });
}

// Reset settings to defaults
function resetSettings() {
  if (!confirm('Are you sure you want to reset all settings to defaults?')) {
    return;
  }

  chrome.storage.local.remove([
    'useCustomLLM',
    'apiKey',
    'modelName',
    'temperature',
    'maxTokens'
  ], () => {
    // Reset UI
    document.getElementById('use-custom-llm').classList.remove('active');
    document.getElementById('llm-settings').style.display = 'none';
    document.getElementById('api-key').value = '';
    document.getElementById('model-name').value = '';
    document.getElementById('temperature').value = 0.7;
    document.getElementById('temp-value').textContent = '0.7';
    document.getElementById('max-tokens').value = '';

    showAlert('Settings reset to defaults', 'success');
    
    setTimeout(() => {
      document.getElementById('alert').style.display = 'none';
    }, 3000);
  });
}

// Show alert message
function showAlert(message, type) {
  const alert = document.getElementById('alert');
  alert.textContent = message;
  alert.className = `alert ${type}`;
  alert.style.display = 'block';
}

// Test custom model connection
async function testConnection() {
  const apiKey = document.getElementById('api-key').value.trim();
  const modelName = document.getElementById('model-name').value.trim();
  const temperature = parseFloat(document.getElementById('temperature').value);
  const maxTokens = parseInt(document.getElementById('max-tokens').value) || null;

  if (!apiKey) {
    showAlert('Please enter an API key', 'error');
    return;
  }

  if (!modelName) {
    showAlert('Please enter a model name', 'error');
    return;
  }

  const btn = document.getElementById('test-connection');
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Testing...`;

  try {
    const response = await fetch('http://127.0.0.1:8000/api/v1/ping/model', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        model_name: modelName,
        model_temperature: temperature,
        model_max_tokens: maxTokens
      })
    });

    const result = await response.json();

    if (result.result === true) {
      showAlert(result.message, 'success');
      // Show green button and tick icon for 2 seconds
      btn.classList.remove('btn-secondary');
      btn.classList.add('btn-success');
      btn.innerHTML = `<span style="font-size:1.2em;vertical-align:middle;">&#10003;</span> Success!`;
      setTimeout(() => {
        btn.classList.remove('btn-success');
        btn.classList.add('btn-secondary');
        btn.textContent = originalText;
      }, 2000);
    } else {
      showAlert(result.message, 'error');
    }
  } catch (error) {
    showAlert(`Connection test failed: ${error.message}`, 'error');
    btn.disabled = false;
    btn.textContent = originalText;
  } finally {
    // Only re-enable if not in success state (handled by setTimeout)
    if (!btn.classList.contains('btn-success')) {
      btn.disabled = false;
      btn.textContent = originalText;
    } else {
      setTimeout(() => {
        btn.disabled = false;
      }, 2000);
    }
  }
}
