// Chat Interface Component
// Based on chat.html and chat.js:26-233

import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage as ChatMessageType, SUGGESTED_QUESTIONS } from '../../types/chat';
import { ChatMessage } from './ChatMessage';

interface ChatInterfaceProps {
  sessionId: string | null;
  messages: ChatMessageType[];
  isInitialized: boolean;
  isLoading: boolean;
  hasUserMessage: boolean;
  onSendMessage: (message: string) => void;
  onInitialize?: (cleanFile: File, errorFile: File) => void;
  databaseInfo?: {
    clean_flights_count?: number;
    error_flights_count?: number;
    total_flights?: number;
  };
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  messages,
  isInitialized,
  isLoading,
  hasUserMessage,
  onSendMessage,
  onInitialize,
  databaseInfo
}) => {
  const [inputValue, setInputValue] = useState('');
  const [cleanFile, setCleanFile] = useState<File | null>(null);
  const [errorFile, setErrorFile] = useState<File | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && isInitialized && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    if (isInitialized && !isLoading) {
      onSendMessage(question);
    }
  };

  const handleInitialize = () => {
    if (cleanFile && errorFile && onInitialize) {
      onInitialize(cleanFile, errorFile);
    }
  };

  // Keyboard shortcut: Ctrl+Enter to submit
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleSubmit(e as any);
    }
  };

  return (
    <div className="chat-interface">
      {/* Messages Area */}
      <div className="chat-messages" id="chatMessages">
        {!isInitialized && onInitialize ? (
          <div className="welcome-card">
            <h2 className="welcome-title">Welcome to Flight Operations AI Assistant</h2>
            <p className="welcome-subtitle">
              Upload your flight data and start analyzing with natural language queries powered by AI.
            </p>

            {/* File Upload Section */}
            <div className="file-upload-section">
              <h3 className="upload-title">📂 Upload Your Data Files</h3>
              <div className="file-inputs">
                <div className="file-input-group">
                  <label htmlFor="cleanFlightsFile" className="file-label">
                    Clean Flights CSV
                  </label>
                  <input
                    type="file"
                    id="cleanFlightsFile"
                    accept=".csv"
                    onChange={(e) => setCleanFile(e.target.files?.[0] || null)}
                    className="file-input"
                  />
                  {cleanFile && (
                    <div className="file-selected">✓ {cleanFile.name}</div>
                  )}
                </div>
                <div className="file-input-group">
                  <label htmlFor="errorFlightsFile" className="file-label">
                    Error Flights CSV
                  </label>
                  <input
                    type="file"
                    id="errorFlightsFile"
                    accept=".csv"
                    onChange={(e) => setErrorFile(e.target.files?.[0] || null)}
                    className="file-input"
                  />
                  {errorFile && (
                    <div className="file-selected">✓ {errorFile.name}</div>
                  )}
                </div>
              </div>
              <button
                onClick={handleInitialize}
                disabled={!cleanFile || !errorFile}
                className="init-button"
              >
                Initialize Chat Session
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Welcome Message with Database Info */}
            {messages.length === 0 && databaseInfo && (
              <div className="welcome-card initialized">
                <h2 className="welcome-title">✈️ Chat Session Ready!</h2>
                <p className="welcome-subtitle">
                  Your flight data has been loaded. Ask me anything about your flights!
                </p>
                <div className="database-stats">
                  {databaseInfo.clean_flights_count !== undefined && (
                    <div className="stat-item">
                      <span className="stat-label">Clean Flights:</span>
                      <span className="stat-value">{databaseInfo.clean_flights_count}</span>
                    </div>
                  )}
                  {databaseInfo.error_flights_count !== undefined && (
                    <div className="stat-item">
                      <span className="stat-label">Error Flights:</span>
                      <span className="stat-value">{databaseInfo.error_flights_count}</span>
                    </div>
                  )}
                  {databaseInfo.total_flights !== undefined && (
                    <div className="stat-item">
                      <span className="stat-label">Total Flights:</span>
                      <span className="stat-value">{databaseInfo.total_flights}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Chat Messages */}
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="loading-message">
                <div className="loading-spinner"></div>
                <span>AI is thinking...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Suggested Questions - Show only before user sends their first message */}
      {isInitialized && !hasUserMessage && (
        <div className="suggested-questions">
          <h3 className="suggestions-title">💡 Try asking:</h3>
          <div className="suggestions-grid">
            {SUGGESTED_QUESTIONS.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                className="suggestion-item"
                disabled={isLoading}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Input */}
      {isInitialized && (
        <div className="chat-input-container">
          <form onSubmit={handleSubmit} className="chat-form">
            <div className="input-wrapper">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about your flight data..."
                className="chat-input"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="send-button"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            </div>
          </form>
          <div className="input-hint">
            Press <kbd>Ctrl + Enter</kbd> to send
          </div>
        </div>
      )}

      <style jsx>{`
        .chat-interface {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #f8fafc;
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 2rem;
          min-height: 400px;
        }

        .welcome-card {
          background: white;
          border: 2px solid #e2e8f0;
          border-radius: 1rem;
          padding: 2.5rem;
          text-align: center;
          max-width: 600px;
          margin: 0 auto;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .welcome-card.initialized {
          background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
          border-color: #c7d2fe;
        }

        .welcome-title {
          font-size: 1.75rem;
          font-weight: 700;
          color: #1e293b;
          margin: 0 0 1rem 0;
        }

        .welcome-subtitle {
          font-size: 1rem;
          color: #64748b;
          margin: 0 0 2rem 0;
          line-height: 1.6;
        }

        .file-upload-section {
          margin-top: 2rem;
        }

        .upload-title {
          font-size: 1.125rem;
          font-weight: 600;
          color: #475569;
          margin: 0 0 1.5rem 0;
        }

        .file-inputs {
          display: grid;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        .file-input-group {
          text-align: left;
        }

        .file-label {
          display: block;
          font-size: 0.875rem;
          font-weight: 600;
          color: #374151;
          margin-bottom: 0.5rem;
        }

        .file-input {
          display: block;
          width: 100%;
          padding: 0.75rem;
          border: 2px solid #cbd5e1;
          border-radius: 0.5rem;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .file-input:hover {
          border-color: #6366f1;
        }

        .file-selected {
          margin-top: 0.5rem;
          font-size: 0.8125rem;
          color: #10b981;
          font-weight: 600;
        }

        .init-button {
          padding: 0.875rem 2rem;
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
          border: none;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 0.9375rem;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .init-button:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
          transform: translateY(-2px);
        }

        .init-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .database-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 1rem;
          margin-top: 1.5rem;
        }

        .stat-item {
          background: white;
          padding: 1rem;
          border-radius: 0.5rem;
          border: 1px solid #c7d2fe;
        }

        .stat-label {
          display: block;
          font-size: 0.75rem;
          color: #64748b;
          margin-bottom: 0.25rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .stat-value {
          display: block;
          font-size: 1.5rem;
          font-weight: 700;
          color: #4f46e5;
        }

        .loading-message {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.75rem;
          color: #64748b;
          font-size: 0.875rem;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 3px solid #e2e8f0;
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .suggested-questions {
          padding: 1rem 2rem 0;
        }

        .suggestions-title {
          font-size: 0.9375rem;
          font-weight: 600;
          color: #475569;
          margin: 0 0 1rem 0;
        }

        .suggestions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 0.75rem;
        }

        .suggestion-item {
          padding: 0.875rem 1.25rem;
          background: white;
          border: 2px solid #e2e8f0;
          border-radius: 0.5rem;
          text-align: left;
          font-size: 0.8125rem;
          color: #475569;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .suggestion-item:hover:not(:disabled) {
          border-color: #6366f1;
          background: #eef2ff;
          transform: translateY(-2px);
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .suggestion-item:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .chat-input-container {
          padding: 1.5rem 2rem;
          background: white;
          border-top: 1px solid #e2e8f0;
        }

        .chat-form {
          margin-bottom: 0.5rem;
        }

        .input-wrapper {
          display: flex;
          gap: 0.75rem;
        }

        .chat-input {
          flex: 1;
          padding: 0.875rem 1.25rem;
          border: 2px solid #cbd5e1;
          border-radius: 0.5rem;
          font-size: 0.9375rem;
          transition: all 0.2s ease;
        }

        .chat-input:focus {
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .chat-input:disabled {
          background: #f1f5f9;
          cursor: not-allowed;
        }

        .send-button {
          padding: 0.875rem 1.25rem;
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
          border: none;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .send-button:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
          transform: translateY(-2px);
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .input-hint {
          font-size: 0.75rem;
          color: #94a3b8;
          text-align: center;
        }

        .input-hint kbd {
          padding: 0.125rem 0.375rem;
          background: #f1f5f9;
          border: 1px solid #cbd5e1;
          border-radius: 0.25rem;
          font-family: monospace;
          font-size: 0.6875rem;
        }

        /* Custom scrollbar */
        .chat-messages::-webkit-scrollbar {
          width: 10px;
        }

        .chat-messages::-webkit-scrollbar-track {
          background: #f1f5f9;
        }

        .chat-messages::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 5px;
        }

        .chat-messages::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  );
};
