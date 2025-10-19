// Chat Message Component
// Based on chat.js:235-287, chat.html:24, 298-321

import React from 'react';
import { marked } from 'marked';
import { ChatMessage as ChatMessageType } from '../../types/chat';
import { CollapsibleTable } from './CollapsibleTable';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  // Configure marked for safe rendering
  marked.setOptions({
    breaks: true, // Convert \n to <br>
    gfm: true, // GitHub Flavored Markdown
  });

  // Render markdown using marked library
  const renderMarkdown = (text: string) => {
    const html = marked.parse(text);
    return { __html: html };
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

        /* Markdown styling */
        .message-text :global(strong),
        .message-text :global(b) {
          font-weight: 700;
          color: #0f172a;
        }

        .message-text :global(em),
        .message-text :global(i) {
          font-style: italic;
        }

        .message-text :global(h1),
        .message-text :global(h2),
        .message-text :global(h3),
        .message-text :global(h4) {
          font-weight: 700;
          margin: 1rem 0 0.5rem 0;
          color: #0f172a;
        }

        .message-text :global(h1) {
          font-size: 1.5rem;
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 0.5rem;
        }

        .message-text :global(h2) {
          font-size: 1.25rem;
        }

        .message-text :global(h3) {
          font-size: 1.125rem;
        }

        .message-text :global(h4) {
          font-size: 1rem;
        }

        .message-text :global(p) {
          margin: 0.5rem 0;
        }

        .message-text :global(ul),
        .message-text :global(ol) {
          margin: 0.5rem 0;
          padding-left: 1.5rem;
        }

        .message-text :global(li) {
          margin: 0.25rem 0;
        }

        .message-text :global(code) {
          background: #f1f5f9;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
          font-family: 'Courier New', Courier, monospace;
          font-size: 0.875rem;
          color: #e11d48;
        }

        .message-text :global(pre) {
          background: #1e293b;
          color: #e2e8f0;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 0.75rem 0;
        }

        .message-text :global(pre code) {
          background: transparent;
          padding: 0;
          color: #e2e8f0;
          font-size: 0.8125rem;
        }

        .message-text :global(blockquote) {
          border-left: 4px solid #cbd5e1;
          padding-left: 1rem;
          margin: 0.75rem 0;
          color: #64748b;
          font-style: italic;
        }

        .message-text :global(a) {
          color: #6366f1;
          text-decoration: underline;
          transition: color 0.2s ease;
        }

        .message-text :global(a:hover) {
          color: #4f46e5;
        }

        .message-text :global(table) {
          border-collapse: collapse;
          width: 100%;
          margin: 0.75rem 0;
        }

        .message-text :global(th),
        .message-text :global(td) {
          border: 1px solid #e2e8f0;
          padding: 0.5rem;
          text-align: left;
        }

        .message-text :global(th) {
          background: #f8fafc;
          font-weight: 600;
        }

        .message-text :global(hr) {
          border: none;
          border-top: 2px solid #e2e8f0;
          margin: 1rem 0;
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
