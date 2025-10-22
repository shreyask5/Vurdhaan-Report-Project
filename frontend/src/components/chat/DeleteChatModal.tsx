// Delete Chat Confirmation Modal
// Confirms chat deletion with warning message

import React from 'react';

interface DeleteChatModalProps {
  chatName: string;
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting?: boolean;
}

export const DeleteChatModal: React.FC<DeleteChatModalProps> = ({
  chatName,
  isOpen,
  onConfirm,
  onCancel,
  isDeleting = false
}) => {
  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isDeleting) {
      onCancel();
    }
  };

  return (
    <>
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="modal-content">
          {/* Icon */}
          <div className="modal-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="32" height="32">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>

          {/* Title */}
          <h2 className="modal-title">Delete Chat?</h2>

          {/* Message */}
          <p className="modal-message">
            Are you sure you want to delete <strong>"{chatName}"</strong>?
            <br />
            This action cannot be undone. All messages and data will be permanently deleted.
          </p>

          {/* Actions */}
          <div className="modal-actions">
            <button
              onClick={onCancel}
              className="cancel-button"
              disabled={isDeleting}
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              className="delete-button"
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <div className="button-spinner"></div>
                  Deleting...
                </>
              ) : (
                'Delete Chat'
              )}
            </button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .modal-content {
          background: white;
          border-radius: 1rem;
          padding: 2rem;
          max-width: 420px;
          width: calc(100% - 2rem);
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
          animation: slideUp 0.3s ease;
          text-align: center;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .modal-icon {
          width: 64px;
          height: 64px;
          margin: 0 auto 1.5rem;
          background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #dc2626;
        }

        .modal-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: #1e293b;
          margin: 0 0 1rem 0;
        }

        .modal-message {
          font-size: 0.9375rem;
          color: #64748b;
          line-height: 1.6;
          margin: 0 0 2rem 0;
        }

        .modal-message strong {
          color: #1e293b;
          font-weight: 600;
        }

        .modal-actions {
          display: flex;
          gap: 0.75rem;
          justify-content: center;
        }

        .cancel-button,
        .delete-button {
          padding: 0.75rem 1.5rem;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 0.9375rem;
          cursor: pointer;
          transition: all 0.2s ease;
          border: none;
          min-width: 120px;
        }

        .cancel-button {
          background: #f1f5f9;
          color: #475569;
          border: 1px solid #e2e8f0;
        }

        .cancel-button:hover:not(:disabled) {
          background: #e2e8f0;
          border-color: #cbd5e1;
        }

        .cancel-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .delete-button {
          background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .delete-button:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(220, 38, 38, 0.3);
          transform: translateY(-1px);
        }

        .delete-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
          transform: none;
        }

        .button-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};
