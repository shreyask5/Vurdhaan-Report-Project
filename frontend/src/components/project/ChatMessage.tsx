// Chat Message Component
// Based on chat.js:235-287, chat.html:24, 298-321

import React from 'react';
import { ChatMessage as ChatMessageType } from '../../types/chat';
import { CollapsibleTable } from './CollapsibleTable';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  // Simple markdown-like rendering for bold and line breaks
  const renderMarkdown = (text: string) => {
    // Convert **bold** to <strong>
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert line breaks
    formatted = formatted.replace(/\n/g, '<br/>');
    return { __html: formatted };
  };

  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-content-wrapper">
        <div className="message-role">
          {isUser ? 'You' : 'AI Assistant'}
        </div>
        <div className="message-content">
          <div
            className="message-text"
            dangerouslySetInnerHTML={renderMarkdown(message.content)}
          />

          {/* SQL Query Display */}
          {message.sql_query && (
            <div className="sql-display">
              <div className="sql-header">Generated SQL Query:</div>
              <pre className="sql-code">{message.sql_query}</pre>
            </div>
          )}

          {/* Table Data */}
          {message.table_data && message.table_data.length > 0 && (
            <CollapsibleTable
              data={message.table_data}
              filename={`query_${message.id}.csv`}
            />
          )}
        </div>
        <div className="message-timestamp">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>

      <style jsx>{`
        .chat-message {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
          animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .message-avatar {
          flex-shrink: 0;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
        }

        .user-message .message-avatar {
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        }

        .assistant-message .message-avatar {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }

        .message-content-wrapper {
          flex: 1;
          min-width: 0;
        }

        .message-role {
          font-size: 0.75rem;
          font-weight: 600;
          color: #64748b;
          margin-bottom: 0.5rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .message-content {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.75rem;
          padding: 1rem 1.25rem;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .user-message .message-content {
          background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
          border-color: #c7d2fe;
        }

        .assistant-message .message-content {
          background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
          border-color: #bbf7d0;
        }

        .message-text {
          color: #1e293b;
          line-height: 1.6;
          font-size: 0.9375rem;
        }

        .message-text :global(strong) {
          font-weight: 700;
          color: #0f172a;
        }

        .sql-display {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .sql-header {
          font-size: 0.75rem;
          font-weight: 600;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 0.5rem;
        }

        .sql-code {
          background: #1e293b;
          color: #e2e8f0;
          padding: 1rem;
          border-radius: 0.5rem;
          font-size: 0.8125rem;
          font-family: 'Courier New', Courier, monospace;
          overflow-x: auto;
          margin: 0;
          line-height: 1.5;
        }

        .message-timestamp {
          font-size: 0.6875rem;
          color: #94a3b8;
          margin-top: 0.5rem;
        }

        /* Custom scrollbar for SQL code */
        .sql-code::-webkit-scrollbar {
          height: 6px;
        }

        .sql-code::-webkit-scrollbar-track {
          background: #0f172a;
        }

        .sql-code::-webkit-scrollbar-thumb {
          background: #475569;
          border-radius: 3px;
        }

        .sql-code::-webkit-scrollbar-thumb:hover {
          background: #64748b;
        }
      `}</style>
    </div>
  );
};
