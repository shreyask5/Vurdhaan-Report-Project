// Chat History Item Component
// Individual chat item in the sidebar with rename and delete functionality

import React, { useState, useRef, useEffect } from 'react';
import { ChatMetadata } from '../../types/chat';

interface ChatHistoryItemProps {
  chat: ChatMetadata;
  isActive: boolean;
  onSelect: () => void;
  onRename: (newName: string) => void;
  onDelete: () => void;
}

export const ChatHistoryItem: React.FC<ChatHistoryItemProps> = ({
  chat,
  isActive,
  onSelect,
  onRename,
  onDelete
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(chat.name);
  const [showActions, setShowActions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditValue(chat.name);
    setIsEditing(true);
    setShowActions(false);
  };

  const handleSaveEdit = () => {
    const trimmedValue = editValue.trim();
    if (trimmedValue && trimmedValue !== chat.name) {
      onRename(trimmedValue);
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditValue(chat.name);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <>
      <div
        className={`chat-item ${isActive ? 'active' : ''}`}
        onClick={isEditing ? undefined : onSelect}
        onMouseEnter={() => !isEditing && setShowActions(true)}
        onMouseLeave={() => !isEditing && setShowActions(false)}
      >
        {/* Chat Icon */}
        <div className="chat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>

        {/* Chat Name (editable) */}
        <div className="chat-info">
          {isEditing ? (
            <input
              ref={inputRef}
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleSaveEdit}
              onKeyDown={handleKeyDown}
              className="chat-name-input"
              maxLength={100}
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <>
              <div className="chat-name">{chat.name}</div>
              <div className="chat-meta">
                <span className="chat-date">{formatDate(chat.updated_at)}</span>
                {chat.message_count > 0 && (
                  <>
                    <span className="meta-separator">•</span>
                    <span className="message-count">{chat.message_count} msgs</span>
                  </>
                )}
              </div>
            </>
          )}
        </div>

        {/* Action Buttons */}
        {!isEditing && showActions && (
          <div className="chat-actions">
            <button
              onClick={handleStartEdit}
              className="action-button"
              title="Rename chat"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button
              onClick={handleDelete}
              className="action-button delete"
              title="Delete chat"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        .chat-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          margin-bottom: 0.5rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
        }

        .chat-item:hover {
          background: #f8fafc;
          border-color: #cbd5e1;
          transform: translateX(2px);
        }

        .chat-item.active {
          background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
          border-color: #a5b4fc;
          box-shadow: 0 2px 4px rgba(99, 102, 241, 0.1);
        }

        .chat-item.active .chat-name {
          color: #4f46e5;
          font-weight: 600;
        }

        .chat-icon {
          flex-shrink: 0;
          width: 32px;
          height: 32px;
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
        }

        .chat-item.active .chat-icon {
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
        }

        .chat-info {
          flex: 1;
          min-width: 0;
        }

        .chat-name {
          font-size: 0.875rem;
          font-weight: 500;
          color: #1e293b;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 0.25rem;
        }

        .chat-name-input {
          width: 100%;
          padding: 0.25rem 0.5rem;
          border: 2px solid #6366f1;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          outline: none;
          background: white;
        }

        .chat-meta {
          display: flex;
          align-items: center;
          gap: 0.375rem;
          font-size: 0.75rem;
          color: #94a3b8;
        }

        .meta-separator {
          font-size: 0.5rem;
        }

        .chat-date,
        .message-count {
          white-space: nowrap;
        }

        .chat-actions {
          display: flex;
          gap: 0.25rem;
          align-items: center;
        }

        .action-button {
          padding: 0.375rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
        }

        .action-button:hover {
          background: #f1f5f9;
          border-color: #cbd5e1;
          color: #475569;
        }

        .action-button.delete:hover {
          background: #fef2f2;
          border-color: #fecaca;
          color: #dc2626;
        }
      `}</style>
    </>
  );
};
