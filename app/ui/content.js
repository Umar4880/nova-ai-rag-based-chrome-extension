// Content script that injects chatbot into web pages
let chatbotContainer = null;
let isOpen = false;
let sessionInfo = null;
let markdownRenderer = null;

// Initialize chatbot when page loads
(function init() {
  console.log('[CONTENT] Content script initializing...');
  // MarkdownRenderer is loaded from markdown-renderer.js (injected first in manifest)
  markdownRenderer = new MarkdownRenderer();
  createChatbotUI();
  requestSessionInfo();
  console.log('[CONTENT] Content script initialized');
})();

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[CONTENT] Message received from background:', request.type);
  
  if (request.type === 'SESSION_CREATED') {
    sessionInfo = {
      sessionId: request.sessionId,
      userId: request.userId,
      pageUrl: request.pageUrl,
      chatStarted: true
    };
    console.log('[CONTENT] Session info received and stored:', sessionInfo);
    sendResponse({ success: true });
  } else if (request.type === 'OPEN_CHAT') {
    if (!isOpen) {
      toggleChat();
    }
    sendResponse({ success: true });
  }
  return true;
});

// Request session info from background script
function requestSessionInfo() {
  console.log('[CONTENT] Requesting session info from background...');
  chrome.runtime.sendMessage({ type: 'GET_SESSION_INFO' }, (response) => {
    if (chrome.runtime.lastError) {
      console.debug('[CONTENT] Background script not ready:', chrome.runtime.lastError.message);
      return;
    }
    if (response) {
      sessionInfo = response;
      console.log('[CONTENT] Session info loaded from background:', sessionInfo);
    } else {
      console.log('[CONTENT] No existing session found in background');
    }
  });
}



// Create chatbot UI
function createChatbotUI() {
  // Create container
  chatbotContainer = document.createElement('div');
  chatbotContainer.id = 'ai-chat-assistant-container';
  chatbotContainer.className = 'ai-chat-container';
  
  chatbotContainer.innerHTML = `
    <div class="ai-chat-toggle" id="ai-chat-toggle">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2ZM20 16H6L4 18V4H20V16Z" fill="white"/>
        <path d="M7 9H17V11H7V9ZM7 12H14V14H7V12Z" fill="white"/>
      </svg>
    </div>
    
    <div class="ai-chat-window" id="ai-chat-window" style="display: none;">
      <div class="ai-chat-header">
        <div class="ai-chat-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="white"/>
            <circle cx="12" cy="12" r="3" fill="white"/>
          </svg>
          <span>AI Assistant</span>
        </div>
        <div class="ai-chat-actions">
          <button class="ai-chat-clear" id="ai-chat-clear" title="Clear history">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19ZM19 4H15.5L14.5 3H9.5L8.5 4H5V6H19V4Z" fill="white"/>
            </svg>
          </button>
          <button class="ai-chat-minimize" id="ai-chat-minimize" title="Minimize">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 13H5V11H19V13Z" fill="white"/>
            </svg>
          </button>
        </div>
      </div>
      
      <div class="ai-chat-messages" id="ai-chat-messages">
        <div class="ai-chat-welcome">
          <p>Hi! I'm your AI assistant. How can I help you today?</p>
        </div>
      </div>
      
      <div class="ai-chat-input-container">
        <textarea 
          class="ai-chat-input" 
          id="ai-chat-input" 
          placeholder="Type your message here..."
          rows="1"
        ></textarea>
        <button class="ai-chat-send" id="ai-chat-send">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="white"/>
          </svg>
        </button>
      </div>
    </div>
  `;
  
  document.body.appendChild(chatbotContainer);
  
  // Add event listeners
  document.getElementById('ai-chat-toggle').addEventListener('click', toggleChat);
  document.getElementById('ai-chat-minimize').addEventListener('click', toggleChat);
  document.getElementById('ai-chat-send').addEventListener('click', sendMessage);
  document.getElementById('ai-chat-clear').addEventListener('click', clearHistory);
  
  const input = document.getElementById('ai-chat-input');
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  // Auto-resize textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });
}

// Toggle chat window
function toggleChat() {
  isOpen = !isOpen;
  const chatWindow = document.getElementById('ai-chat-window');
  const toggle = document.getElementById('ai-chat-toggle');
  
  if (isOpen) {
    chatWindow.style.display = 'flex';
    toggle.style.display = 'none';
    document.getElementById('ai-chat-input').focus();
  } else {
    chatWindow.style.display = 'none';
    toggle.style.display = 'flex';
  }
}

// Send message
async function sendMessage() {
  const input = document.getElementById('ai-chat-input');
  const message = input.value.trim();
  
  if (!message) return;
  
  console.log('[CONTENT] sendMessage called, sessionInfo:', sessionInfo);
  
  // Check if session exists before sending
  if (!sessionInfo || !sessionInfo.sessionId) {
    console.error('[CONTENT] No sessionInfo found!');
    addMessage('No active session found. Please start chat first by clicking on the extension icon.', 'bot', true);
    return;
  }
  
  // Add user message to chat
  addMessage(message, 'user');
  
  // Clear input
  input.value = '';
  input.style.height = 'auto';
  
  // Show typing indicator
  const typingId = showTypingIndicator();
  
  console.log('[CONTENT] Sending message to background...');
  
  // Send message to background script
  chrome.runtime.sendMessage(
    { type: 'SEND_MESSAGE', message: message },
    (response) => {
      removeTypingIndicator(typingId);
      console.log('[CONTENT] Received response from background:', response);
      if (chrome.runtime.lastError) {
        addMessage('Sorry, there was an error processing your message. (Extension context invalidated)', 'bot', true);
        console.error('Error:', chrome.runtime.lastError.message);
        return;
      }
      if (response && response.error) {
        console.error('[CONTENT] Response contains error:', response.error);
        if (response.error === 'No active session found. Please start chat first.') {
          addMessage('No active session found. Please start chat first by clicking on extension icon.', 'bot', true);
        } else {
          addMessage('Sorry, there was an error processing your message.', 'bot', true);
        }
        console.error('Error:', response.error);
      } else if (response && response.data) {
            console.log('[CONTENT] Adding bot response to chat');
            addMessage(response.data.response, 'bot');
      }
    }
  );
}

// Add message to chat
function addMessage(text, sender, isError = false) {
  const messagesContainer = document.getElementById('ai-chat-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `ai-chat-message ai-chat-message-${sender}`;
  
  if (isError) {
    messageDiv.classList.add('ai-chat-message-error');
  }
  
  const avatar = document.createElement('div');
  avatar.className = 'ai-chat-avatar';
  avatar.textContent = sender === 'user' ? '👤' : '🤖';
  
  const content = document.createElement('div');
  content.className = 'ai-chat-message-content markdown-content';
  
  // Render markdown for bot messages, plain text for user messages
  if (sender === 'bot' && !isError) {
    content.innerHTML = markdownRenderer.render(text);
  } else {
    content.textContent = text;
  }
  
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(content);
  
  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  // Typeset math for bot messages
  if (sender === 'bot' && !isError) {
    console.log('[CONTENT] Math rendering handled by KaTeX');
    markdownRenderer.typeset(messagesContainer);
  }
}

// Copy code to clipboard function
window.copyCodeToClipboard = function(codeId) {
    const codeBlock = document.getElementById(`code-${codeId}`);
    const code = codeBlock.textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const btn = codeBlock.parentElement.querySelector('.copy-code-btn');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Copied!
        `;
        btn.classList.add('copied');
        
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy code:', err);
    });
};

// Show typing indicator
function showTypingIndicator() {
  const messagesContainer = document.getElementById('ai-chat-messages');
  const typingDiv = document.createElement('div');
  const id = 'typing-' + Date.now();
  typingDiv.id = id;
  typingDiv.className = 'ai-chat-message ai-chat-message-bot';
  
  typingDiv.innerHTML = `
    <div class="ai-chat-avatar">🤖</div>
    <div class="ai-chat-typing">
      <span></span>
      <span></span>
      <span></span>
    </div>
  `;
  
  messagesContainer.appendChild(typingDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  return id;
}

// Remove typing indicator
function removeTypingIndicator(id) {
  const typingDiv = document.getElementById(id);
  if (typingDiv) {
    typingDiv.remove();
  }
}

// Clear chat history
function clearHistory() {
  if (!confirm('Are you sure you want to clear the chat history?')) {
    return;
  }
  
  chrome.runtime.sendMessage(
    { type: 'CLEAR_HISTORY' },
    (response) => {
      if (chrome.runtime.lastError) {
        alert('Failed to clear history: ' + chrome.runtime.lastError.message);
        return;
      }
      if (response && response.error) {
        alert('Failed to clear history: ' + response.error);
      } else {
        // Clear messages from UI
        const messagesContainer = document.getElementById('ai-chat-messages');
        messagesContainer.innerHTML = `
          <div class="ai-chat-welcome">
            <p>Hi! I'm your AI assistant. How can I help you today?</p>
          </div>
        `;
      }
    }
  );
}
