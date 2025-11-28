// Popup script
document.addEventListener('DOMContentLoaded', () => {
  loadUserInfo();
  loadModelInfo();
  updateChatButton();
  setupEventListeners();
});

// Load user information
function loadUserInfo() {
  chrome.storage.local.get(['userId'], (result) => {
    const userIdElement = document.getElementById('user-id');
    if (result.userId) {
      // Show truncated user ID
      const truncatedId = result.userId.substring(0, 12) + '...';
      userIdElement.textContent = truncatedId;
      userIdElement.title = result.userId; // Full ID on hover
    } else {
      userIdElement.textContent = 'Not set';
    }
  });
}

// Load model information
function loadModelInfo() {
  chrome.storage.local.get(['useCustomLLM', 'modelName'], (result) => {
    const modelDisplay = document.getElementById('model-display');
    
    if (result.useCustomLLM && result.modelName) {
      modelDisplay.textContent = result.modelName;
      modelDisplay.classList.add('custom-model');
    } else {
      modelDisplay.textContent = 'Base Model';
      modelDisplay.classList.remove('custom-model');
    }
  });
}

// Update chat button text based on session state
function updateChatButton() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.runtime.sendMessage({ 
        type: 'GET_SESSION_INFO',
        tabId: tabs[0].id 
      }, (response) => {
        const btn = document.getElementById('open-chat');
        if (response && response.chatStarted) {
          btn.textContent = 'Open Chat';
        } else {
          btn.textContent = 'Start Chat';
        }
      });
    }
  });
}

// Setup event listeners
function setupEventListeners() {
  // Open/Start chat button
  document.getElementById('open-chat').addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        const btn = document.getElementById('open-chat');
        if (btn.textContent === 'Start Chat') {
          // Show spinner/indicator
          btn.disabled = true;
          btn.innerHTML = `<span class="spinner" style="display:inline-block;width:18px;height:18px;border:2px solid #fff;border-top:2px solid #888;border-radius:50%;animation:spin 1s linear infinite;margin-right:8px;vertical-align:middle;"></span> Creating...`;

          chrome.runtime.sendMessage({ 
            type: 'START_CHAT',
            url: tabs[0].url,
            tabId: tabs[0].id
          }, (startResponse) => {
            // Restore button state
            btn.disabled = false;
            btn.textContent = 'Open Chat';

            if (chrome.runtime.lastError) {
              console.error('Failed to start chat:', chrome.runtime.lastError.message);
              alert('Failed to start chat. Please try again.');
              return;
            }
            if (!startResponse || !startResponse.success) {
              console.error('Failed to start session:', startResponse?.error);
              alert('Failed to start session. Please try again.');
              return;
            }
            // Session created successfully, now open chat
            chrome.tabs.sendMessage(tabs[0].id, { type: 'OPEN_CHAT' }, (response) => {
              if (chrome.runtime.lastError) {
                console.warn('Failed to open chat:', chrome.runtime.lastError.message);
                alert('Please refresh the page and try again.');
              } else {
                window.close();
              }
            });
          });
        } else {
          // Just open existing chat
          chrome.tabs.sendMessage(tabs[0].id, { type: 'OPEN_CHAT' }, (response) => {
            if (chrome.runtime.lastError) {
              console.warn('Failed to open chat:', chrome.runtime.lastError.message);
              alert('Please refresh the page and try again.');
            } else {
              window.close();
            }
          });
        }
      }
    });
  });

  // Settings button
  document.getElementById('settings').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
}