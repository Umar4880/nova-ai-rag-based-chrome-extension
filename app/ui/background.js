// Background service worker for Chrome extension
const API_BASE_URL = 'http://127.0.0.1:8000';

// Store active chat sessions per tab
const activeSessions = new Map(); // tabId -> { sessionId, userId, pageUrl, chatStarted }

// Generate unique user ID on installation
chrome.runtime.onInstalled.addListener(() => {
  const userId = generateUserId();
  chrome.storage.local.set({ userId: userId }, () => {
    console.log('User ID generated:', userId);
  });
});

// Listen for tab updates (URL changes)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // Only process when we have a URL (ignore other update events like loading, title changes, etc.)
  if (!tab.url) {
    return;
  }
  
  console.log('[BACKGROUND] Tab updated - tabId:', tabId, 'status:', changeInfo.status, 'url:', tab.url);
  
  const session = activeSessions.get(tabId);
  
  // If there's an active session, check if URL has changed
  if (session) {
    if (session.pageUrl !== tab.url) {
      // URL changed - need to create new session
      console.log('[BACKGROUND] URL changed detected:', session.pageUrl, '->', tab.url);
      if (changeInfo.status === 'complete') {
        handleTabUpdate(tabId, tab.url);
      }
    } else {
      // URL is same - retain existing session, do nothing
      console.log('[BACKGROUND] Tab updated but URL unchanged - retaining session');
    }
  } else {
    // No active session - only handle when page is fully loaded
    if (changeInfo.status === 'complete') {
      handleTabUpdate(tabId, tab.url);
    }
  }
});

// Listen for tab activation (switching between tabs)
chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (tab.url) {
      notifyContentScriptOfState(activeInfo.tabId);
    }
  });
});

// Listen for tab removal (cleanup)
chrome.tabs.onRemoved.addListener((tabId) => {
  console.log('[BACKGROUND] ⚠️ Tab removed event fired for tabId:', tabId);
  console.log('[BACKGROUND] activeSessions BEFORE removal:', Array.from(activeSessions.entries()));
  
  // Clear history when tab is closed
  const session = activeSessions.get(tabId);
  if (session) {
    console.log('[BACKGROUND] Clearing session for removed tab:', tabId);
    fetch(`${API_BASE_URL}/api/v1/session/${session.sessionId}/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: session.sessionId,
        user_id: session.userId
      })
    }).catch((err) => {
      console.warn('Failed to clear history on tab close:', err);
    });
  }
  activeSessions.delete(tabId);
  chrome.storage.session.remove([`session_${tabId}`]);
  console.log('[BACKGROUND] activeSessions AFTER removal:', Array.from(activeSessions.entries()));
});

// Clear all sessions when Chrome is closed or extension is unloaded
chrome.runtime.onSuspend.addListener(() => {
  for (const [tabId, session] of activeSessions.entries()) {
    fetch(`${API_BASE_URL}/api/v1/session/${session.sessionId}/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: session.sessionId,
        user_id: session.userId
      })
    }).catch((err) => {
      console.warn('Failed to clear history on Chrome close:', err);
    });
  }
  activeSessions.clear();
});

// Handle tab URL updates
async function handleTabUpdate(tabId, newUrl) {
  // Skip chrome:// and edge:// URLs
  if (newUrl.startsWith('chrome://') || newUrl.startsWith('edge://') || newUrl.startsWith('about:')) {
    console.log('[BACKGROUND] Skipping internal URL:', newUrl);
    return;
  }

  const session = activeSessions.get(tabId);
  
  if (session && session.chatStarted) {
    // Session exists - check if URL actually changed
    if (session.pageUrl !== newUrl) {
      console.log('[BACKGROUND] URL changed in active chat tab - creating new session');
      console.log('[BACKGROUND] Old URL:', session.pageUrl);
      console.log('[BACKGROUND] New URL:', newUrl);
      
      // Delete old session from backend
      try {
        await fetch(`${API_BASE_URL}/api/v1/session/${session.sessionId}/delete`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: session.sessionId,
            user_id: session.userId
          })
        });
        console.log('[BACKGROUND] Old session deleted from backend');
      } catch (err) {
        console.warn('[BACKGROUND] Failed to delete old session:', err);
      }
      
      // Create new session for new URL
      await createSession(tabId, newUrl, true);
    } else {
      console.log('[BACKGROUND] URL unchanged, keeping existing session');
    }
  } else {
    // No active session - show "Start Chat" button
    console.log('[BACKGROUND] No active session - sending SHOW_START_CHAT_BUTTON');
    chrome.tabs.sendMessage(tabId, {
      type: 'SHOW_START_CHAT_BUTTON',
      url: newUrl
    }, (response) => {
      if (chrome.runtime.lastError) {
        // Content script not ready yet, ignore
        console.debug('[BACKGROUND] Content script not ready:', chrome.runtime.lastError.message);
      }
    });
  }
}

// Notify content script of current state
function notifyContentScriptOfState(tabId) {
  const session = activeSessions.get(tabId);
  chrome.tabs.sendMessage(tabId, {
    type: 'UPDATE_CHAT_STATE',
    chatStarted: session ? session.chatStarted : false,
    sessionInfo: session || null
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.debug('Content script not ready:', chrome.runtime.lastError.message);
    }
  });
}

// Create session (called when user clicks "Start Chat" or URL changes in active chat)
async function createSession(tabId, url, isAutoUpdate = false) {
  console.log('[BACKGROUND] createSession called - tabId:', tabId, 'url:', url, 'isAutoUpdate:', isAutoUpdate);
  console.log('[BACKGROUND] activeSessions BEFORE createSession:', Array.from(activeSessions.entries()));
  
  try {
    const { userId } = await chrome.storage.local.get(['userId']);
    if (!userId) {
      console.error('User ID not found');
      return;
    }

    const sessionId = `session-${Date.now()}-${tabId}`;
    
    console.log('[BACKGROUND] Creating new session with ID:', sessionId);
    
    // Show loading state in content script
    chrome.tabs.sendMessage(tabId, {
      type: 'SESSION_LOADING',
      isAutoUpdate: isAutoUpdate
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.debug('Content script not ready:', chrome.runtime.lastError.message);
      }
    });

    // Create new session
    const response = await fetch(`${API_BASE_URL}/api/v1/session/new`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        user_id: userId,
        page_url: url
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Session created:', data);
      
      // Store in memory
      activeSessions.set(tabId, {
        sessionId: sessionId,
        userId: userId,
        pageUrl: url,
        chatStarted: true
      });

      console.log('[BACKGROUND] Session created and stored for tabId:', tabId);
      console.log('[BACKGROUND] activeSessions now contains:', Array.from(activeSessions.entries()));
      
      // Also persist to chrome.storage as backup
      chrome.storage.session.set({
        [`session_${tabId}`]: {
          sessionId: sessionId,
          userId: userId,
          pageUrl: url,
          chatStarted: true
        }
      }).catch(err => console.warn('[BACKGROUND] Failed to persist session to storage:', err));

      // Notify content script
      chrome.tabs.sendMessage(tabId, {
        type: 'SESSION_CREATED',
        sessionId: sessionId,
        userId: userId,
        pageUrl: url
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn('Failed to notify content script of session creation:', chrome.runtime.lastError.message);
        }
      });
    } else {
      throw new Error('Failed to create session');
    }
  } catch (error) {
    console.error('Error creating session:', error);
    chrome.tabs.sendMessage(tabId, {
      type: 'SESSION_ERROR',
      error: error.message
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.warn('Failed to notify content script of session error:', chrome.runtime.lastError.message);
      }
    });
  }
}

// Generate unique user ID
function generateUserId() {
  return 'user-' + Date.now() + '-' + Math.random().toString(36).substring(2, 15);
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'START_CHAT') {
    // User clicked "Start Chat" button in popup
    const tabId = request.tabId || sender.tab?.id;
    if (tabId) {
      createSession(tabId, request.url, false)
        .then(() => {
          const session = activeSessions.get(tabId);
          sendResponse({ success: true, session: session });
        })
        .catch((error) => {
          sendResponse({ success: false, error: error.message });
        });
    } else {
      sendResponse({ success: false, error: 'No tab ID found' });
    }
    return true;
  } else if (request.type === 'SEND_MESSAGE') {
    handleChatMessage(request, sender.tab.id)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  } else if (request.type === 'GET_SESSION_INFO') {
    const tabId = request.tabId || sender.tab?.id;
    if (tabId) {
      let session = activeSessions.get(tabId);
      
      // If not in memory, try to restore from chrome.storage
      if (!session) {
        chrome.storage.session.get([`session_${tabId}`]).then(stored => {
          if (stored[`session_${tabId}`]) {
            session = stored[`session_${tabId}`];
            activeSessions.set(tabId, session);
            console.log('[BACKGROUND] Session restored from storage for GET_SESSION_INFO:', session);
          }
          sendResponse(session || null);
        });
        return true; // Will respond asynchronously
      } else {
        sendResponse(session);
      }
    } else {
      sendResponse(null);
    }
    return true;
  } else if (request.type === 'CLEAR_HISTORY') {
    handleClearHistory(request, sender.tab.id)
      .then(response => sendResponse(response))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
});

// Handle chat message
async function handleChatMessage(request, tabId) {
  console.log('[BACKGROUND] handleChatMessage called for tabId:', tabId);
  console.log('[BACKGROUND] activeSessions contents:', Array.from(activeSessions.entries()));
  
  try {
    let session = activeSessions.get(tabId);
    
    // If not in memory, try to restore from chrome.storage
    if (!session) {
      console.log('[BACKGROUND] Session not in memory, checking chrome.storage...');
      const stored = await chrome.storage.session.get([`session_${tabId}`]);
      if (stored[`session_${tabId}`]) {
        session = stored[`session_${tabId}`];
        activeSessions.set(tabId, session);
        console.log('[BACKGROUND] Session restored from storage:', session);
      }
    }
    
    console.log('[BACKGROUND] Session for tabId', tabId, ':', session);
    
    if (!session) {
      console.error('[BACKGROUND] No session found for tabId:', tabId);
      throw new Error('No active session found. Please start chat first.');
    }

    // Get LLM settings
    const llmSettings = await chrome.storage.local.get([
      'useCustomLLM',
      'apiKey',
      'modelName',
      'temperature',
      'maxTokens'
    ]);

    const requestBody = {
      message: request.message,
      session_id: session.sessionId,
      user_id: session.userId
    };

    // Add custom LLM settings if enabled
    if (llmSettings.useCustomLLM) {
      if (llmSettings.apiKey) requestBody.api_key = llmSettings.apiKey;
      if (llmSettings.modelName) requestBody.model_name = llmSettings.modelName;
      if (llmSettings.temperature !== null && llmSettings.temperature !== undefined) {
        requestBody.model_temperature = llmSettings.temperature;
      }
      if (llmSettings.maxTokens) requestBody.model_max_tokens = llmSettings.maxTokens;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/c/${session.sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const data = await response.json();
    console.log('[BACKGROUND] Message sent successfully, activeSessions:', Array.from(activeSessions.entries()));
    return { success: true, data: data };
  } catch (error) {
    console.error('[BACKGROUND] Error sending message:', error);
    throw error;
  }
}

// Handle clear history
async function handleClearHistory(request, tabId) {
  try {
    const session = activeSessions.get(tabId);
    
    if (!session) {
      throw new Error('No active session found');
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/session/${session.sessionId}/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: session.sessionId,
        user_id: session.userId
      })
    });

    if (!response.ok) {
      throw new Error('Failed to clear history');
    }

    const data = await response.json();
    return { success: true, data: data };
  } catch (error) {
    console.error('Error clearing history:', error);
    throw error;
  }
}
