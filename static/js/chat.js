// Chat Application JavaScript
class FlightOpsChat {
    constructor() {
        this.sessionId = null;
        this.isInitialized = false;
        this.messageHistory = [];
        
        // DOM elements
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.chatInputContainer = document.getElementById('chatInputContainer');
        this.suggestedQuestions = document.getElementById('suggestedQuestions');
        this.fileUploadSection = document.getElementById('fileUploadSection');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.sessionInfo = document.getElementById('sessionInfo');
        
        // File inputs
        this.cleanFlightsFile = document.getElementById('cleanFlightsFile');
        this.errorFlightsFile = document.getElementById('errorFlightsFile');
        
        // Bind methods
        this.initializeChat = this.initializeChat.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.askQuestion = this.askQuestion.bind(this);
        
        // Check for session_id in URL parameters
        this.checkUrlParams();
    }
    
    checkUrlParams() {
        console.log('🌐 [DEBUG] Chat JS → Checking URL parameters');
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');
        
        if (sessionId) {
            console.log('🎯 [DEBUG] Chat JS → Session ID found in URL:', sessionId);
            // Auto-initialize with existing session
            this.sessionId = sessionId;
            this.autoInitializeFromSession(sessionId);
        } else {
            console.log('ℹ️ [DEBUG] Chat JS → No session_id in URL parameters');
        }
    }
    
    async autoInitializeFromSession(sessionId) {
        try {
            console.log('🔄 [DEBUG] Chat JS → Auto-initializing from session:', sessionId);
            this.logDebug('Starting auto-initialization', { sessionId });
            
            this.showLoading();
            
            // Get session status
            console.log('📡 [DEBUG] Chat JS → Fetching session status from server');
            this.logDebug('Fetching session status');
            
            const response = await fetch(`/chat/${sessionId}/status`);
            
            if (!response.ok) {
                console.log('❌ [DEBUG] Chat JS → Session status fetch failed:', response.status);
                this.logError('Session status fetch failed', { status: response.status, statusText: response.statusText });
                throw new Error(`Session not found or expired (Status: ${response.status})`);
            }
            
            const sessionData = await response.json();
            console.log('✅ [DEBUG] Chat JS → Session status received:', sessionData);
            console.log('🗄️ [DEBUG] Chat JS → Database info:', sessionData.database_info);
            this.logDebug('Session status received', sessionData);
            
            // Update UI to show session is active
            this.isInitialized = true;
            
            // Check if methods exist before calling them
            console.log('🔧 [DEBUG] Chat JS → Updating UI components');
            this.logDebug('Starting UI updates');
            
            if (typeof this.hideFileUploadSection === 'function') {
                this.hideFileUploadSection();
                console.log('✅ [DEBUG] Chat JS → hideFileUploadSection() called successfully');
            } else {
                console.log('⚠️ [DEBUG] Chat JS → hideFileUploadSection() method not found, skipping');
                this.logDebug('hideFileUploadSection method not found - hiding file section manually');
                if (this.fileUploadSection) {
                    this.fileUploadSection.style.display = 'none';
                }
            }
            
            if (typeof this.showChatInterface === 'function') {
                this.showChatInterface();
                console.log('✅ [DEBUG] Chat JS → showChatInterface() called successfully');
            } else {
                console.log('⚠️ [DEBUG] Chat JS → showChatInterface() method not found, showing chat elements manually');
                this.logDebug('showChatInterface method not found - showing chat elements manually');
                this.showChatElementsManually();
            }
            
            if (typeof this.updateSessionInfo === 'function') {
                this.updateSessionInfo(sessionData);
                console.log('✅ [DEBUG] Chat JS → updateSessionInfo() called successfully');
            } else {
                console.log('⚠️ [DEBUG] Chat JS → updateSessionInfo() method not found, skipping');
                this.logDebug('updateSessionInfo method not found');
            }
            
            this.hideLoading();
            console.log('🎉 [DEBUG] Chat JS → Chat interface ready for queries');
            this.logDebug('Chat interface ready for queries');
            
            // Show welcome message
            const welcomeMessage = `Chat session initialized! Your database contains:\n• ${sessionData.database_info?.clean_flights?.row_count || 0} clean flight records\n• ${sessionData.database_info?.error_flights?.row_count || 0} error records\n\nYou can now ask questions about your flight data.`;
            this.addMessage('system', welcomeMessage);
            
        } catch (error) {
            console.error('💥 [DEBUG] Chat JS → Auto-initialization failed:', error);
            console.error('💥 [DEBUG] Chat JS → Error stack:', error.stack);
            this.logError('Auto-initialization failed', { 
                error: error.message, 
                stack: error.stack,
                sessionId: sessionId 
            });
            
            this.hideLoading();
            this.addMessage('system', `Failed to load session: ${error.message}`);
        }
    }
    
    async initializeChat() {
        // Show loading
        this.showLoading();
        
        try {
            // Get files
            const cleanFile = this.cleanFlightsFile.files[0];
            const errorFile = this.errorFlightsFile.files[0];
            
            if (!cleanFile || !errorFile) {
                throw new Error('Please select both CSV files');
            }
            
            // Create form data
            const formData = new FormData();
            formData.append('clean_data', cleanFile);
            formData.append('error_data', errorFile);
            
            // Upload files first
            const uploadResponse = await fetch('/upload_files', {
                method: 'POST',
                body: formData
            });
            
            if (!uploadResponse.ok) {
                throw new Error('Failed to upload files');
            }
            
            const uploadData = await uploadResponse.json();
            
            // Initialize chat session
            const initResponse = await fetch('/chat/initialize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.generateSessionId(),
                    clean_data_csv: uploadData.clean_csv_path,
                    error_data_csv: uploadData.error_csv_path
                })
            });
            
            if (!initResponse.ok) {
                throw new Error('Failed to initialize chat session');
            }
            
            const initData = await initResponse.json();
            
            // Update state
            this.sessionId = initData.session_id;
            this.isInitialized = true;
            
            // Update UI
            this.fileUploadSection.style.display = 'none';
            this.chatInputContainer.style.display = 'block';
            this.suggestedQuestions.style.display = 'block';
            
            // Show session info
            this.updateSessionInfo(initData);
            
            // Add welcome message
            this.addMessage('assistant', `Great! I've loaded your flight data. I found ${initData.database_info.clean_flights.row_count} clean flight records and ${initData.database_info.error_flights.row_count} error records. What would you like to know about your data?`);
            
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    async sendMessage(event) {
        event.preventDefault();
        
        const message = this.chatInput.value.trim();
        if (!message || !this.isInitialized) return;
        
        // Clear input
        this.chatInput.value = '';
        
        // Add user message
        this.addMessage('user', message);
        
        // Show loading
        this.showLoading();
        
        try {
            // Send query
            const response = await fetch(`/chat/${this.sessionId}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: message })
            });
            
            if (!response.ok) {
                throw new Error('Failed to process query');
            }
            
            const data = await response.json();
            
            // Add assistant response
            this.addAssistantResponse(data);
            
        } catch (error) {
            this.showError('Failed to process your query. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? 'U' : 'A';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = window.markdownit().render(text);
        
        content.appendChild(textDiv);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    addAssistantResponse(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message assistant';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'A';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        // Add response text
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.innerHTML = window.markdownit().render(data.response);
        content.appendChild(textDiv);
        
        // Add SQL query if available
        if (data.sql) {
            const sqlDiv = document.createElement('div');
            sqlDiv.className = 'message-sql';
            sqlDiv.innerHTML = `<strong>SQL Query:</strong><br><code>${this.escapeHtml(data.sql)}</code>`;
            content.appendChild(sqlDiv);
        }
        
        // Add results if available
        if (data.results && data.results.data && data.results.data.length > 0) {
            const resultsDiv = document.createElement('div');
            resultsDiv.className = 'message-results';
            
            // Create table
            const table = this.createResultsTable(data.results.data);
            resultsDiv.appendChild(table);
            
            // Add summary
            if (data.results.total_rows > data.results.displayed_rows) {
                const summary = document.createElement('div');
                summary.className = 'results-summary';
                summary.textContent = `Showing ${data.results.displayed_rows} of ${data.results.total_rows} total results`;
                resultsDiv.appendChild(summary);
            }
            
            content.appendChild(resultsDiv);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    createResultsTable(data) {
        const table = document.createElement('table');
        table.className = 'results-table';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        const columns = Object.keys(data[0]);
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        
        data.slice(0, 10).forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = row[col] !== null ? row[col] : '';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        return table;
    }
    
    askQuestion(question) {
        this.chatInput.value = question;
        this.chatInput.focus();
    }
    
    updateSessionInfo(data) {
        const expiresAt = new Date(data.expires_at);
        const hoursLeft = Math.round((expiresAt - new Date()) / (1000 * 60 * 60));
        
        this.sessionInfo.innerHTML = `
            Session ID: ${data.session_id.substring(0, 8)}... | 
            Expires in: ${hoursLeft} hours
        `;
    }
    
    showLoading() {
        this.loadingOverlay.style.display = 'flex';
    }
    
    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Missing UI methods - added for compatibility
    hideFileUploadSection() {
        console.log('🔧 [DEBUG] Chat JS → Hiding file upload section');
        this.logDebug('hideFileUploadSection called');
        
        if (this.fileUploadSection) {
            this.fileUploadSection.style.display = 'none';
            console.log('✅ [DEBUG] Chat JS → File upload section hidden');
        } else {
            console.log('⚠️ [DEBUG] Chat JS → File upload section element not found');
            this.logDebug('File upload section element not found');
        }
    }
    
    showChatInterface() {
        console.log('🔧 [DEBUG] Chat JS → Showing chat interface');
        this.logDebug('showChatInterface called');
        
        // Show chat input container
        if (this.chatInputContainer) {
            this.chatInputContainer.style.display = 'block';
            console.log('✅ [DEBUG] Chat JS → Chat input container shown');
        } else {
            console.log('⚠️ [DEBUG] Chat JS → Chat input container not found');
        }
        
        // Show suggested questions
        if (this.suggestedQuestions) {
            this.suggestedQuestions.style.display = 'block';
            console.log('✅ [DEBUG] Chat JS → Suggested questions shown');
        } else {
            console.log('⚠️ [DEBUG] Chat JS → Suggested questions element not found');
        }
        
        // Show session info
        if (this.sessionInfo) {
            this.sessionInfo.style.display = 'block';
            console.log('✅ [DEBUG] Chat JS → Session info shown');
        } else {
            console.log('⚠️ [DEBUG] Chat JS → Session info element not found');
        }
    }
    
    showChatElementsManually() {
        console.log('🔧 [DEBUG] Chat JS → Manually showing chat elements');
        this.logDebug('showChatElementsManually called');
        
        // Try to find and show common chat elements
        const elementsToShow = [
            'chatInputContainer',
            'suggestedQuestions', 
            'sessionInfo',
            'chatMessages'
        ];
        
        elementsToShow.forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                element.style.display = 'block';
                console.log(`✅ [DEBUG] Chat JS → ${elementId} shown manually`);
            } else {
                console.log(`⚠️ [DEBUG] Chat JS → ${elementId} not found`);
            }
        });
        
        // Hide file upload elements
        const elementsToHide = [
            'fileUploadSection',
            'uploadSection'
        ];
        
        elementsToHide.forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                element.style.display = 'none';
                console.log(`✅ [DEBUG] Chat JS → ${elementId} hidden manually`);
            } else {
                console.log(`⚠️ [DEBUG] Chat JS → ${elementId} not found`);
            }
        });
    }
    
    // Debug logging methods
    logDebug(message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level: 'DEBUG',
            component: 'FlightOpsChat',
            message,
            data,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        // Log to console
        console.log(`🐛 [${timestamp}] ${message}`, data || '');
        
        // Send to server for logging
        this.sendLogToServer(logEntry).catch(err => {
            console.warn('Failed to send debug log to server:', err);
        });
    }
    
    logError(message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level: 'ERROR',
            component: 'FlightOpsChat',
            message,
            data,
            url: window.location.href,
            userAgent: navigator.userAgent,
            stack: data?.stack || new Error().stack
        };
        
        // Log to console
        console.error(`🚨 [${timestamp}] ${message}`, data || '');
        
        // Send to server for logging
        this.sendLogToServer(logEntry).catch(err => {
            console.warn('Failed to send error log to server:', err);
        });
    }
    
    async sendLogToServer(logEntry) {
        try {
            await fetch('/api/log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(logEntry)
            });
        } catch (error) {
            // Silently fail - don't want logging to break the app
            console.warn('Failed to send log to server:', error);
        }
    }
    
    // Method to dump current state for debugging
    dumpState() {
        const state = {
            sessionId: this.sessionId,
            isInitialized: this.isInitialized,
            messageHistory: this.messageHistory,
            domElements: {
                chatMessages: !!this.chatMessages,
                chatInput: !!this.chatInput,
                chatInputContainer: !!this.chatInputContainer,
                suggestedQuestions: !!this.suggestedQuestions,
                fileUploadSection: !!this.fileUploadSection,
                loadingOverlay: !!this.loadingOverlay,
                sessionInfo: !!this.sessionInfo
            },
            url: window.location.href,
            timestamp: new Date().toISOString()
        };
        
        console.log('🔍 [DEBUG] FlightOpsChat State Dump:', state);
        this.logDebug('State dump requested', state);
        
        return state;
    }
}

// Initialize chat application
const chatApp = new FlightOpsChat();

// Global error handling for unhandled JavaScript errors
window.addEventListener('error', (event) => {
    const errorInfo = {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString()
    };
    
    console.error('🚨 [GLOBAL ERROR]', errorInfo);
    
    // Send to chat app logger if available
    if (chatApp && typeof chatApp.logError === 'function') {
        chatApp.logError('Unhandled JavaScript error', errorInfo);
    }
});

// Global error handling for unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    const errorInfo = {
        reason: event.reason,
        promise: event.promise,
        stack: event.reason?.stack,
        timestamp: new Date().toISOString()
    };
    
    console.error('🚨 [UNHANDLED PROMISE REJECTION]', errorInfo);
    
    // Send to chat app logger if available  
    if (chatApp && typeof chatApp.logError === 'function') {
        chatApp.logError('Unhandled promise rejection', errorInfo);
    }
});

// Debug function to inspect chat app state from console
window.debugChatApp = function() {
    if (chatApp && typeof chatApp.dumpState === 'function') {
        return chatApp.dumpState();
    } else {
        console.error('Chat app not initialized or dumpState method not available');
        return null;
    }
};

// Global functions for HTML onclick handlers
function initializeChat() {
    try {
        console.log('🎯 [DEBUG] Global function: initializeChat called');
        chatApp.initializeChat();
    } catch (error) {
        console.error('🚨 [ERROR] initializeChat failed:', error);
        if (chatApp && typeof chatApp.logError === 'function') {
            chatApp.logError('initializeChat global function failed', { error: error.message, stack: error.stack });
        }
    }
}

function sendMessage(event) {
    try {
        console.log('🎯 [DEBUG] Global function: sendMessage called');
        chatApp.sendMessage(event);
    } catch (error) {
        console.error('🚨 [ERROR] sendMessage failed:', error);
        if (chatApp && typeof chatApp.logError === 'function') {
            chatApp.logError('sendMessage global function failed', { error: error.message, stack: error.stack });
        }
    }
}

function askQuestion(question) {
    try {
        console.log('🎯 [DEBUG] Global function: askQuestion called with:', question);
        chatApp.askQuestion(question);
    } catch (error) {
        console.error('🚨 [ERROR] askQuestion failed:', error);
        if (chatApp && typeof chatApp.logError === 'function') {
            chatApp.logError('askQuestion global function failed', { error: error.message, stack: error.stack, question });
        }
    }
}

// Add keyboard shortcut for sending message
document.addEventListener('keydown', (e) => {
    try {
        if (e.key === 'Enter' && e.ctrlKey) {
            const form = document.querySelector('.chat-form');
            if (form) {
                form.dispatchEvent(new Event('submit'));
            }
        }
    } catch (error) {
        console.error('🚨 [ERROR] Keyboard shortcut failed:', error);
        if (chatApp && typeof chatApp.logError === 'function') {
            chatApp.logError('Keyboard shortcut failed', { error: error.message, stack: error.stack });
        }
    }
});

// Log initialization
console.log('🚀 [DEBUG] Chat application JavaScript loaded');
if (chatApp && typeof chatApp.logDebug === 'function') {
    chatApp.logDebug('Chat application JavaScript loaded and initialized', {
        hasSessionId: !!chatApp.sessionId,
        isInitialized: chatApp.isInitialized,
        url: window.location.href
    });
}