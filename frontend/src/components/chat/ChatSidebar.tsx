// Chat Sidebar Component
// Displays list of chats with create, rename, and delete functionality

import React, { useState } from 'react';
import { ChatMetadata } from '../../types/chat';
import { ChatHistoryItem } from './ChatHistoryItem';

interface ChatSidebarProps {
  chats: ChatMetadata[];
  activeChatId: string | null;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onCreateChat: () => void;
  onSelectChat: (chatId: string) => void;
  onRenameChat: (chatId: string, newName: string) => void;
  onDeleteChat: (chatId: string) => void;
  isLoading?: boolean;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  chats,
  activeChatId,
  isCollapsed,
  onToggleCollapse,
  onCreateChat,
  onSelectChat,
  onRenameChat,
  onDeleteChat,
  isLoading = false
}) => {
  return (
    <>
      <div className={`chat-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
        {/* Header */}
        <div className="sidebar-header">
          {!isCollapsed && (
            <>
              <h2 className="sidebar-title">Chat History</h2>
              <button
                onClick={onCreateChat}
                className="new-chat-button"
                disabled={isLoading}
                title="Create new chat"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                New Chat
              </button>
            </>
          )}
        </div>

        {/* Chat List */}
        {!isCollapsed && (
          <div className="chat-list">
            {isLoading && chats.length === 0 ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <span>Loading chats...</span>
              </div>
            ) : chats.length === 0 ? (
              <div className="empty-state">
                <p>No chats yet</p>
                <p className="empty-hint">Click "New Chat" to start</p>
              </div>
            ) : (
              chats.map((chat) => (
                <ChatHistoryItem
                  key={chat.id}
                  chat={chat}
                  isActive={chat.id === activeChatId}
                  onSelect={() => onSelectChat(chat.id)}
                  onRename={(newName) => onRenameChat(chat.id, newName)}
                  onDelete={() => onDeleteChat(chat.id)}
                />
              ))
            )}
          </div>
        )}

        {/* Toggle Button */}
        <button
          onClick={onToggleCollapse}
          className="collapse-toggle"
          title={isCollapsed ? 'Show sidebar' : 'Hide sidebar'}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            width="20"
            height="20"
            style={{ transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)' }}
          >
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
      </div>

      <style jsx>{`
        .chat-sidebar {
          width: 280px;
          height: 100%;
          background: #ffffff;
          border-right: 1px solid #e2e8f0;
          display: flex;
          flex-direction: column;
          transition: all 0.3s ease;
          position: relative;
        }

        .chat-sidebar.collapsed {
          width: 0;
          border-right: none;
          overflow: hidden;
        }

        .sidebar-header {
          padding: 1.25rem 1rem;
          border-bottom: 1px solid #e2e8f0;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }

        .sidebar-title {
          font-size: 1rem;
          font-weight: 700;
          color: #1e293b;
          margin: 0 0 0.75rem 0;
        }

        .new-chat-button {
          width: 100%;
          padding: 0.625rem 1rem;
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
          border: none;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .new-chat-button:hover:not(:disabled) {
          box-shadow: 0 6px 12px -2px rgba(99, 102, 241, 0.3);
          transform: translateY(-1px);
        }

        .new-chat-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .chat-list {
          flex: 1;
          overflow-y: auto;
          padding: 0.75rem;
        }

        .loading-state,
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 2rem 1rem;
          text-align: center;
          color: #64748b;
        }

        .loading-spinner {
          width: 24px;
          height: 24px;
          border: 3px solid #e2e8f0;
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin-bottom: 0.75rem;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .loading-state span {
          font-size: 0.875rem;
          font-weight: 500;
        }

        .empty-state p {
          margin: 0;
          font-size: 0.875rem;
        }

        .empty-hint {
          margin-top: 0.25rem;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .collapse-toggle {
          position: absolute;
          top: 1.5rem;
          right: -12px;
          width: 24px;
          height: 24px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          z-index: 10;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .collapse-toggle:hover {
          background: #f8fafc;
          border-color: #cbd5e1;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
        }

        .collapse-toggle svg {
          transition: transform 0.3s ease;
        }

        /* Custom scrollbar */
        .chat-list::-webkit-scrollbar {
          width: 6px;
        }

        .chat-list::-webkit-scrollbar-track {
          background: #f1f5f9;
        }

        .chat-list::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
        }

        .chat-list::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </>
  );
};
