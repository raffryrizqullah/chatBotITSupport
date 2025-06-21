// Enhanced Chatbot Script with improved functionality and error handling

class ChatbotController {
  constructor() {
    this.initializeElements();
    this.initializeVariables();
    this.bindEvents();
    this.loadChatHistory();
  }

  initializeElements() {
    this.chatbotToggleButton = document.querySelector(".chatbot-toggle-button");
    this.chatbotCloseButton = document.querySelector(".chatbot-close-button");
    this.chatMessagesContainer = document.querySelector(".chat-messages");
    this.chatInputField = document.querySelector(".chat-input-area textarea");
    this.sendMessageButton = document.querySelector(".chat-input-area span");
    
    // Validate required elements
    const requiredElements = [
      this.chatbotToggleButton,
      this.chatMessagesContainer,
      this.chatInputField,
      this.sendMessageButton
    ];
    
    if (requiredElements.some(element => !element)) {
      console.error("Required chatbot elements not found");
      return;
    }
  }

  initializeVariables() {
    this.currentUserMessage = null;
    this.initialChatInputHeight = this.chatInputField.scrollHeight;
    this.isWaitingForResponse = false;
    this.messageHistory = [];
    this.retryCount = 0;
    this.maxRetries = 3;
    
    // Configuration
    this.config = {
      maxMessageLength: 1000,
      typingDelay: 600,
      autoScrollDelay: 100,
      storageKey: 'chatbot_history',
      typingStyle: 'dots' // 'dots', 'wave', 'bubble' - change according to preference
    };
  }

  bindEvents() {
    // Input field events
    this.chatInputField.addEventListener("input", () => this.handleInputResize());
    this.chatInputField.addEventListener("keydown", (event) => this.handleKeyDown(event));
    this.chatInputField.addEventListener("paste", (event) => this.handlePaste(event));

    // Button events
    this.sendMessageButton.addEventListener("click", () => this.handleChat());
    
    if (this.chatbotCloseButton) {
      this.chatbotCloseButton.addEventListener("click", () => this.closeChatbot());
    }
    
    this.chatbotToggleButton.addEventListener("click", () => this.toggleChatbot());

    // Window events
    window.addEventListener("beforeunload", () => this.saveChatHistory());
    window.addEventListener("resize", () => this.handleWindowResize());
  }

  // Enhanced input handling
  handleInputResize() {
    this.chatInputField.style.height = `${this.initialChatInputHeight}px`;
    this.chatInputField.style.height = `${this.chatInputField.scrollHeight}px`;
    
    // Update send button visibility based on content
    this.updateSendButtonState();
  }

  handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && window.innerWidth > 800) {
      event.preventDefault();
      this.handleChat();
    } else if (event.key === "Escape") {
      this.closeChatbot();
    }
  }

  handlePaste(event) {
    // Handle paste events and validate content length
    setTimeout(() => {
      const content = this.chatInputField.value;
      if (content.length > this.config.maxMessageLength) {
        this.showNotification(`Message too long. Maximum ${this.config.maxMessageLength} characters.`, 'warning');
        this.chatInputField.value = content.substring(0, this.config.maxMessageLength);
      }
      this.handleInputResize();
    }, 0);
  }

  handleWindowResize() {
    // Adjust chatbot layout for different screen sizes
    if (window.innerWidth <= 490) {
      document.body.classList.add('mobile-view');
    } else {
      document.body.classList.remove('mobile-view');
    }
  }

  // Enhanced message validation
  validateMessage(message) {
    if (!message || message.trim().length === 0) {
      this.showNotification("Please enter a message first.", 'warning');
      return false;
    }

    if (message.length > this.config.maxMessageLength) {
      this.showNotification(`Message too long. Maximum ${this.config.maxMessageLength} characters.`, 'warning');
      return false;
    }

    // Basic spam detection
    if (this.isSpamMessage(message)) {
      this.showNotification("Please wait before sending another message.", 'warning');
      return false;
    }

    return true;
  }

  isSpamMessage(message) {
    const now = Date.now();
    const recentMessages = this.messageHistory.filter(msg => 
      now - msg.timestamp < 5000 && msg.type === 'outgoing'
    );
    
    // Check for repeated messages
    const duplicateCount = recentMessages.filter(msg => msg.content === message).length;
    return duplicateCount >= 2;
  }

  // Enhanced chat handling
  async handleChat() {
    if (this.isWaitingForResponse) {
      this.showNotification("Processing previous message...", 'info');
      return;
    }

    this.currentUserMessage = this.chatInputField.value.trim();
    
    if (!this.validateMessage(this.currentUserMessage)) {
      return;
    }

    // Disable input and show loading state
    this.setInputState(false);
    this.clearInput();

    // Add outgoing message
    const outgoingMessage = this.createChatListItem(this.currentUserMessage, "outgoing");
    this.addMessageToChat(outgoingMessage);
    
    // Add to history
    this.addToHistory(this.currentUserMessage, 'outgoing');

    // Show typing indicator after delay
    setTimeout(() => {
      const incomingMessage = this.createChatListItem("", "incoming", true);
      this.addMessageToChat(incomingMessage);
      this.generateResponse(incomingMessage);
    }, this.config.typingDelay);
  }

  // Enhanced message creation
  createChatListItem(messageText, messageType, isTyping = false) {
    const chatListItem = document.createElement("li");
    chatListItem.classList.add("chat", messageType);
    
    let chatContent;
    if (messageType === "outgoing") {
      chatContent = `<p></p>`;
      chatListItem.setAttribute('data-timestamp', new Date().toLocaleTimeString());
    } else {
      chatContent = `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
      if (isTyping) {
        chatListItem.classList.add('typing');
      }
    }
    
    chatListItem.innerHTML = chatContent;
    
    if (isTyping) {
      this.createTypingIndicator(chatListItem.querySelector("p"));
    } else {
      chatListItem.querySelector("p").textContent = messageText;
    }
    
    return chatListItem;
  }

  createTypingIndicator(element) {
    // Choose typing indicator style (you can change this)
    const indicatorStyle = this.config.typingStyle || 'dots'; // 'dots', 'wave', 'bubble'
    
    switch(indicatorStyle) {
      case 'wave':
        element.innerHTML = `
          <div class="typing-indicator-container">
            <div class="typing-text">BSI UII is typing</div>
            <div class="sound-wave">
              <div class="bar"></div>
              <div class="bar"></div>
              <div class="bar"></div>
              <div class="bar"></div>
              <div class="bar"></div>
            </div>
          </div>
        `;
        break;
        
      case 'bubble':
        element.innerHTML = `
          <div class="typing-bubble">
            <div class="typing-text">BSI UII is typing...</div>
          </div>
        `;
        break;
        
      default: // 'dots'
        element.innerHTML = `
          <div class="typing-indicator-container">
            <div class="typing-text">BSI UII is typing...</div>
          </div>
        `;
    }
    
    element.classList.add('typing-animation');
  }

  addMessageToChat(messageElement) {
    this.chatMessagesContainer.appendChild(messageElement);
    this.scrollToBottom();
  }

  // Enhanced response generation with retry logic
  async generateResponse(chatListItem) {
    const messageParagraph = chatListItem.querySelector("p");
    this.isWaitingForResponse = true;

    try {
      const response = await this.sendMessageToServer(this.currentUserMessage);
      
      // Remove typing indicator
      chatListItem.classList.remove('typing');
      messageParagraph.classList.remove('typing-animation');
      
      // Add response with typewriter effect
      await this.typewriterEffect(messageParagraph, response);
      
      // Add to history
      this.addToHistory(response, 'incoming');
      
      this.retryCount = 0; // Reset retry count on success
      
    } catch (error) {
      console.error("Error generating response:", error);
      await this.handleResponseError(messageParagraph, error);
    } finally {
      this.isWaitingForResponse = false;
      this.setInputState(true);
      this.scrollToBottom();
    }
  }

  async sendMessageToServer(message) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    const requestOptions = {
      method: "POST",
      headers: { 
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest"
      },
      body: `msg=${encodeURIComponent(message)}`,
      signal: controller.signal
    };

    try {
      const response = await fetch("/get", requestOptions);
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error (${response.status}): ${errorText}`);
      }
      
      const responseText = await response.text();
      return responseText || "Sorry, I cannot provide a response at this time.";
      
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error("Request timeout. Please try again.");
      }
      
      throw error;
    }
  }

  async handleResponseError(messageParagraph, error) {
    messageParagraph.classList.add("error");
    
    let errorMessage = "An error occurred. ";
    
    if (error.message.includes("timeout")) {
      errorMessage += "Connection timeout. ";
    } else if (error.message.includes("500")) {
      errorMessage += "Server error. ";
    } else if (!navigator.onLine) {
      errorMessage += "No internet connection. ";
    } else {
      errorMessage += error.message + " ";
    }

    // Add retry option if haven't exceeded max retries
    if (this.retryCount < this.maxRetries) {
      errorMessage += `<button class="retry-btn" onclick="chatbot.retryLastMessage()">Try Again (${this.maxRetries - this.retryCount})</button>`;
    }

    messageParagraph.innerHTML = errorMessage;
    this.retryCount++;
  }

  async retryLastMessage() {
    if (this.currentUserMessage) {
      const errorElements = this.chatMessagesContainer.querySelectorAll('.error');
      const lastError = errorElements[errorElements.length - 1];
      if (lastError) {
        const chatItem = lastError.closest('.chat');
        chatItem.classList.remove('typing');
        this.createTypingIndicator(lastError);
        lastError.classList.remove('error');
        await this.generateResponse(chatItem);
      }
    }
  }

  // Typewriter effect for responses
  // Smart URL processing with punctuation handling and HTML cleanup
  processSmartURLs(text) {
    // First, clean any existing HTML artifacts that might interfere
    text = this.cleanHtmlArtifacts(text);
    
    // Enhanced URL regex that handles punctuation at the end
    const urlRegex = /(https?:\/\/[^\s<>"{}|\\^`\[\]]+)/gi;
    
    return text.replace(urlRegex, (match) => {
      // Clean URL by removing trailing punctuation
      let cleanUrl = match;
      let trailingPunctuation = '';
      
      // Remove any HTML attributes that might have been included
      cleanUrl = cleanUrl.replace(/target="_blank".*?>/gi, '');
      cleanUrl = cleanUrl.replace(/rel="[^"]*"/gi, '');
      cleanUrl = cleanUrl.replace(/[<>]/g, '');
      
      // Common punctuation that should not be part of URL
      const punctuationPattern = /([.,;:!?)]*)$/;
      const punctuationMatch = cleanUrl.match(punctuationPattern);
      
      if (punctuationMatch && punctuationMatch[1]) {
        trailingPunctuation = punctuationMatch[1];
        cleanUrl = cleanUrl.slice(0, -trailingPunctuation.length);
      }
      
      // Additional cleanup for common cases
      while (cleanUrl.endsWith('.') || cleanUrl.endsWith(',') || 
             cleanUrl.endsWith(';') || cleanUrl.endsWith(':') ||
             cleanUrl.endsWith('!') || cleanUrl.endsWith('?') ||
             cleanUrl.endsWith(')')) {
        trailingPunctuation = cleanUrl.slice(-1) + trailingPunctuation;
        cleanUrl = cleanUrl.slice(0, -1);
      }
      
      // Validate that it's a proper URL
      if (this.isValidURL(cleanUrl)) {
        return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="auto-link">${cleanUrl}</a>${trailingPunctuation}`;
      }
      
      return match; // Return original if not valid URL
    });
  }
  
  // New function to clean HTML artifacts
  cleanHtmlArtifacts(text) {
    // Remove orphaned HTML attributes that might appear in text
    text = text.replace(/target="_blank"\s*/gi, '');
    text = text.replace(/rel="noopener noreferrer"\s*/gi, '');
    text = text.replace(/rel="[^"]*"\s*/gi, '');
    text = text.replace(/>\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '$1');
    
    // Clean up broken HTML tags
    text = text.replace(/<[^>]*>/g, ' ');
    text = text.replace(/\s+/g, ' ');
    
    return text.trim();
  }
  
  // URL validation helper
  isValidURL(string) {
    try {
      const url = new URL(string);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
      return false;
    }
  }
  
  // Parse markdown to HTML with enhanced cleaning
  parseMarkdown(text) {
    // Clean the input text first
    let html = this.cleanHtmlArtifacts(text);
    
    // Process code blocks first to protect them from other parsing
    const codeBlocks = [];
    html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
      const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
      codeBlocks.push(`<pre><code>${code.trim()}</code></pre>`);
      return placeholder;
    });
    
    // Process inline code
    const inlineCodes = [];
    html = html.replace(/`([^`]+)`/g, (match, code) => {
      const placeholder = `__INLINE_CODE_${inlineCodes.length}__`;
      inlineCodes.push(`<code>${code}</code>`);
      return placeholder;
    });
    
    // Headers (#### Header)
    html = html.replace(/^#### (.*$)/gm, '<h4>$1</h4>')
               .replace(/^### (.*$)/gm, '<h3>$1</h3>')
               .replace(/^## (.*$)/gm, '<h2>$1</h2>')
               .replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Bold text (**text** or __text__)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Italic text (*text* or _text_) - more careful regex
    html = html.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
               .replace(/_([^_\n]+?)_/g, '<em>$1</em>');
    
    // Smart URL detection - detect URLs with punctuation handling
    html = this.processSmartURLs(html);
    
    // Links [text](url) - markdown format
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Horizontal rules (---)
    html = html.replace(/^---$/gm, '<hr>');
    
    // Process lists
    const lines = html.split('\n');
    const processedLines = [];
    let inList = false;
    let listType = '';
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Check for unordered list items
      if (line.match(/^[-*+] (.+)$/)) {
        if (!inList) {
          processedLines.push('<ul>');
          inList = true;
          listType = 'ul';
        } else if (listType !== 'ul') {
          processedLines.push('</' + listType + '>');
          processedLines.push('<ul>');
          listType = 'ul';
        }
        processedLines.push('<li>' + line.replace(/^[-*+] /, '') + '</li>');
      }
      // Check for ordered list items - improved pattern matching
      else if (line.match(/^\d+\.\s+(.+)$/)) {
        if (!inList) {
          processedLines.push('<ol>');
          inList = true;
          listType = 'ol';
        } else if (listType !== 'ol') {
          processedLines.push('</' + listType + '>');
          processedLines.push('<ol>');
          listType = 'ol';
        }
        // Extract content after number and dot, preserving formatting
        const content = line.replace(/^\d+\.\s+/, '');
        processedLines.push('<li>' + content + '</li>');
      }
      // Not a list item
      else {
        if (inList) {
          processedLines.push('</' + listType + '>');
          inList = false;
          listType = '';
        }
        processedLines.push(line);
      }
    }
    
    // Close any remaining open list
    if (inList) {
      processedLines.push('</' + listType + '>');
    }
    
    html = processedLines.join('\n');
    
    // Convert line breaks to <br> (but not around headers and lists)
    html = html.replace(/\n/g, '<br>');
    
    // Clean up extra <br> tags around headers and lists
    html = html.replace(/<br>\s*(<h[1-6]>)/g, '$1')
               .replace(/(<\/h[1-6]>)\s*<br>/g, '$1')
               .replace(/<br>\s*(<[uo]l>)/g, '$1')
               .replace(/(<\/[uo]l>)\s*<br>/g, '$1')
               .replace(/<br>\s*(<li>)/g, '$1')
               .replace(/(<\/li>)\s*<br>/g, '$1');
    
    // Restore code blocks
    codeBlocks.forEach((code, index) => {
      html = html.replace(new RegExp(`__CODE_BLOCK_${index}__`, 'g'), code);
    });
    
    // Restore inline codes
    inlineCodes.forEach((code, index) => {
      html = html.replace(new RegExp(`__INLINE_CODE_${index}__`, 'g'), code);
    });
    
    // Final cleanup to remove any remaining HTML artifacts
    html = this.finalTextCleanup(html);
    
    return html;
  }
  
  // Final text cleanup to ensure clean display
  finalTextCleanup(text) {
    // Remove any remaining HTML attribute fragments
    text = text.replace(/target="_blank"[^>]*>/gi, '');
    text = text.replace(/rel="[^"]*"[^>]*>/gi, '');
    
    // Clean up malformed HTML
    text = text.replace(/<([^>]+)([^>]*target="_blank"[^>]*)>/gi, '<$1>');
    text = text.replace(/<([^>]+)([^>]*rel="[^"]*"[^>]*)>/gi, '<$1>');
    
    // Remove orphaned closing brackets and attributes
    text = text.replace(/>\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, ' $1');
    text = text.replace(/([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*</g, '$1 ');
    
    // Clean up extra spaces
    text = text.replace(/\s+/g, ' ');
    
    return text.trim();
  }

  async typewriterEffect(element, text, speed = 30) {
    // Parse markdown and display immediately for better formatting
    const htmlContent = this.parseMarkdown(text);
    element.innerHTML = htmlContent;
    this.scrollToBottom();
  }

  // Utility methods
  clearInput() {
    this.chatInputField.value = "";
    this.chatInputField.style.height = `${this.initialChatInputHeight}px`;
    this.updateSendButtonState();
  }

  setInputState(enabled) {
    this.chatInputField.disabled = !enabled;
    this.sendMessageButton.style.opacity = enabled ? "1" : "0.5";
    this.sendMessageButton.style.pointerEvents = enabled ? "auto" : "none";
    
    if (enabled) {
      this.chatInputField.focus();
    }
  }

  updateSendButtonState() {
    const hasContent = this.chatInputField.value.trim().length > 0;
    this.sendMessageButton.style.visibility = hasContent ? "visible" : "hidden";
  }

  scrollToBottom() {
    setTimeout(() => {
      this.chatMessagesContainer.scrollTo({
        top: this.chatMessagesContainer.scrollHeight,
        behavior: 'smooth'
      });
    }, this.config.autoScrollDelay);
  }

  toggleChatbot() {
    document.body.classList.toggle("show-chatbot");
    
    if (document.body.classList.contains("show-chatbot")) {
      this.chatInputField.focus();
      this.scrollToBottom();
    }
  }

  closeChatbot() {
    document.body.classList.remove("show-chatbot");
  }

  // Chat history management
  addToHistory(content, type) {
    this.messageHistory.push({
      content,
      type,
      timestamp: Date.now()
    });

    // Keep only last 50 messages to prevent memory issues
    if (this.messageHistory.length > 50) {
      this.messageHistory = this.messageHistory.slice(-50);
    }
  }

  saveChatHistory() {
    try {
      const historyData = {
        messages: this.messageHistory.slice(-20), // Save only last 20 messages
        timestamp: Date.now()
      };
      localStorage.setItem(this.config.storageKey, JSON.stringify(historyData));
    } catch (error) {
      console.warn("Could not save chat history:", error);
    }
  }

  loadChatHistory() {
    try {
      const savedData = localStorage.getItem(this.config.storageKey);
      if (savedData) {
        const historyData = JSON.parse(savedData);
        
        // Only load recent history (within last 24 hours)
        const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
        if (historyData.timestamp > oneDayAgo) {
          this.messageHistory = historyData.messages || [];
        }
      }
    } catch (error) {
      console.warn("Could not load chat history:", error);
    }
  }

  clearChatHistory() {
    this.messageHistory = [];
    localStorage.removeItem(this.config.storageKey);
    
    // Clear chat messages except the initial greeting
    const messages = this.chatMessagesContainer.querySelectorAll('.chat:not(:first-child)');
    messages.forEach(message => message.remove());
    
    this.showNotification("Chat history has been cleared.", 'info');
  }

  // Notification system
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '12px 20px',
      borderRadius: '8px',
      zIndex: '10000',
      fontSize: '14px',
      fontWeight: '500',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      transform: 'translateX(100%)',
      transition: 'transform 0.3s ease'
    });

    // Set colors based on type
    const colors = {
      info: { bg: '#e3f2fd', text: '#1976d2', border: '#2196f3' },
      warning: { bg: '#fff3e0', text: '#f57c00', border: '#ff9800' },
      error: { bg: '#ffebee', text: '#d32f2f', border: '#f44336' },
      success: { bg: '#e8f5e8', text: '#388e3c', border: '#4caf50' }
    };

    const color = colors[type] || colors.info;
    notification.style.backgroundColor = color.bg;
    notification.style.color = color.text;
    notification.style.borderLeft = `4px solid ${color.border}`;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);

    // Auto remove after 4 seconds
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 4000);
  }

  // Public API methods
  sendMessage(message) {
    this.chatInputField.value = message;
    this.handleChat();
  }

  getMessageHistory() {
    return [...this.messageHistory];
  }

  // Change typing indicator style
  setTypingStyle(style) {
    const validStyles = ['dots', 'wave', 'bubble'];
    if (validStyles.includes(style)) {
      this.config.typingStyle = style;
      this.showNotification(`Typing indicator changed to: ${style}`, 'success');
    } else {
      this.showNotification(`Invalid style. Use: ${validStyles.join(', ')}`, 'warning');
    }
  }

  // Demo different typing indicators
  demoTypingIndicators() {
    const styles = ['dots', 'wave', 'bubble'];
    let index = 0;
    
    const demo = () => {
      if (index < styles.length) {
        this.setTypingStyle(styles[index]);
        setTimeout(() => {
          // Create a demo typing message
          const demoMessage = this.createChatListItem("", "incoming", true);
          this.addMessageToChat(demoMessage);
          
          // Remove after 3 seconds and continue demo
          setTimeout(() => {
            demoMessage.remove();
            index++;
            demo();
          }, 3000);
        }, 1000);
      } else {
        this.showNotification('Demo complete! Choose your favorite style.', 'info');
      }
    };
    
    demo();
  }
}

// Initialize chatbot when DOM is loaded
let chatbot;

document.addEventListener('DOMContentLoaded', () => {
  chatbot = new ChatbotController();
  
  // Make it globally accessible for debugging
  window.chatbot = chatbot;
});

// Add CSS for typing indicator and notifications
const additionalStyles = `
  /* Enhanced Typing Indicator */
  .typing-indicator-container {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 0;
    color: #666;
    font-style: italic;
  }

  .typing-text {
    font-size: 13px;
    color: #06337b;
    font-weight: 400;
  }


  /* Enhanced typing animation for message container */
  .chat.typing {
    animation: pulseGlow 2s infinite;
  }

  @keyframes pulseGlow {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
  }

  /* Alternative typing indicator styles */
  .typing-bubble {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 18px;
    padding: 12px 16px;
    margin: 4px 0;
  }

  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }

  /* Pulsing avatar during typing */
  .chat.typing .material-symbols-outlined {
    animation: avatarPulse 1.5s infinite;
  }

  @keyframes avatarPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }

  .retry-btn {
    background: #06337b;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    margin-left: 8px;
    transition: background-color 0.2s;
  }

  .retry-btn:hover {
    background: #044a8a;
  }

  .mobile-view .chatbot {
    height: 100vh !important;
  }

  .notification {
    font-family: "Poppins", sans-serif;
    cursor: pointer;
  }

  .chat[data-timestamp]:hover::after {
    content: attr(data-timestamp);
    position: absolute;
    right: 10px;
    font-size: 11px;
    opacity: 0.6;
    pointer-events: none;
  }

  /* Enhanced message appearance during typing */
  .chat.incoming.typing p {
    min-height: 45px;
    display: flex;
    align-items: center;
    background: linear-gradient(90deg, #f8f9fa, #e9ecef, #f8f9fa);
    background-size: 200% 100%;
    animation: messageShimmer 2s infinite;
  }

  /* Auto-generated link styling */
  .chat.incoming p a.auto-link {
    color: #06337b;
    text-decoration: underline;
    font-weight: 500;
    word-break: break-all;
    transition: all 0.2s ease;
    background: rgba(6, 51, 123, 0.05);
    padding: 1px 3px;
    border-radius: 3px;
  }

  .chat.incoming p a.auto-link:hover {
    color: #044a8a;
    background: rgba(6, 51, 123, 0.1);
    text-decoration: none;
    transform: translateY(-1px);
  }

  .chat.incoming p a.auto-link::before {
    content: "🔗 ";
    font-size: 0.8em;
    opacity: 0.7;
  }

  /* Markdown Styling for AI Responses */
  .chat.incoming p h1,
  .chat.incoming p h2,
  .chat.incoming p h3,
  .chat.incoming p h4 {
    color: #06337b;
    margin: 12px 0 8px 0;
    font-weight: 600;
    line-height: 1.3;
  }

  .chat.incoming p h1 { font-size: 1.4em; }
  .chat.incoming p h2 { font-size: 1.3em; }
  .chat.incoming p h3 { font-size: 1.2em; }
  .chat.incoming p h4 { font-size: 1.1em; }

  .chat.incoming p strong {
    font-weight: 600;
    color: #06337b;
  }

  .chat.incoming p em {
    font-style: italic;
    color: #444;
  }

  .chat.incoming p a {
    color: #06337b;
    text-decoration: underline;
    font-weight: 500;
    transition: color 0.2s ease;
  }

  .chat.incoming p a:hover {
    color: #044a8a;
    text-decoration: none;
  }

  .chat.incoming p ul,
  .chat.incoming p ol {
    margin: 8px 0;
    padding-left: 20px;
  }

  .chat.incoming p li {
    margin: 4px 0;
    line-height: 1.4;
  }

  .chat.incoming p ul li {
    list-style-type: disc;
  }

  .chat.incoming p ol {
    counter-reset: list-counter;
    padding-left: 0;
  }

  .chat.incoming p ol li {
    display: block;
    counter-increment: list-counter;
    list-style: none;
    position: relative;
    margin-left: 20px;
  }

  .chat.incoming p ol li::before {
    content: counter(list-counter) ". ";
    font-weight: 600;
    color: #06337b;
    margin-right: 8px;
    position: absolute;
    left: -20px;
  }

  .chat.incoming p code {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
    color: #e83e8c;
  }

  .chat.incoming p pre {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 12px;
    margin: 8px 0;
    overflow-x: auto;
  }

  .chat.incoming p pre code {
    background: none;
    padding: 0;
    color: #495057;
    font-size: 0.85em;
    line-height: 1.4;
  }

  .chat.incoming p br {
    line-height: 1.6;
  }

  /* Better spacing and readability */
  .chat.incoming p {
    line-height: 1.6;
    word-wrap: break-word;
  }

  .chat.incoming p p {
    margin: 8px 0;
  }

  /* Horizontal line for sections */
  .chat.incoming p hr {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 16px 0;
  }

  /* Better quote styling */
  .chat.incoming p blockquote {
    border-left: 4px solid #06337b;
    padding-left: 12px;
    margin: 8px 0;
    font-style: italic;
    color: #666;
  }

  @keyframes messageShimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }

  /* Sound wave animation (alternative) */
  .sound-wave {
    display: flex;
    align-items: center;
    gap: 2px;
  }

  .sound-wave .bar {
    width: 3px;
    background-color: #06337b;
    border-radius: 2px;
    animation: soundWave 1.2s infinite ease-in-out;
  }

  .sound-wave .bar:nth-child(1) { height: 8px; animation-delay: -0.9s; }
  .sound-wave .bar:nth-child(2) { height: 12px; animation-delay: -0.8s; }
  .sound-wave .bar:nth-child(3) { height: 16px; animation-delay: -0.7s; }
  .sound-wave .bar:nth-child(4) { height: 12px; animation-delay: -0.6s; }
  .sound-wave .bar:nth-child(5) { height: 8px; animation-delay: -0.5s; }

  @keyframes soundWave {
    0%, 40%, 100% { transform: scaleY(0.4); }
    20% { transform: scaleY(1); }
  }
`;

// Inject additional styles
if (!document.getElementById('chatbot-enhanced-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'chatbot-enhanced-styles';
  styleSheet.textContent = additionalStyles;
  document.head.appendChild(styleSheet);
}