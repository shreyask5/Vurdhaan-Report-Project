// Action Buttons Component
// From index4.html:1253-1287

import React from 'react';

interface ActionButtonsProps {
  projectId: string;
  onSaveCorrections: () => void;
  onIgnoreErrors: () => void;
  onDownloadClean: () => void;
  onDownloadErrors: () => void;
  onOpenChat: () => void;
  onStartOver: () => void;
  hasCorrections?: boolean;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onSaveCorrections,
  onIgnoreErrors,
  onDownloadClean,
  onDownloadErrors,
  onOpenChat,
  onStartOver,
  hasCorrections = false
}) => {
  return (
    <div className="action-buttons-container">
      {/* Primary Actions */}
      <div className="button-row primary-actions">
        <button
          className="btn btn-success"
          onClick={onSaveCorrections}
          disabled={!hasCorrections}
        >
          <span className="btn-icon">💾</span> Save Corrections
        </button>
        <button className="btn btn-danger" onClick={onIgnoreErrors}>
          <span className="btn-icon">⚠️</span> Ignore Remaining Errors
        </button>
      </div>

      {/* Download Actions */}
      <div className="button-row download-actions">
        <button className="btn btn-primary" onClick={onDownloadClean}>
          <span className="btn-icon">📥</span> Download Clean Data CSV
        </button>
        <button className="btn btn-primary" onClick={onDownloadErrors}>
          <span className="btn-icon">📥</span> Download Errors CSV
        </button>
      </div>

      {/* Analysis & Reset Actions */}
      <div className="button-row secondary-actions">
        <button className="btn btn-primary btn-highlight" onClick={onOpenChat}>
          <span className="btn-icon">💬</span> Analyze Data with AI Chat
        </button>
        <button className="btn btn-secondary" onClick={onStartOver}>
          <span className="btn-icon">🔄</span> Start Over
        </button>
      </div>

      <style jsx>{`
        .action-buttons-container {
          margin: 2rem 0;
        }

        .button-row {
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
          flex-wrap: wrap;
        }

        .button-row:last-child {
          margin-bottom: 0;
        }

        .btn {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1.5rem;
          border: none;
          border-radius: 0.5rem;
          font-size: 0.9375rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          flex: 1;
          min-width: 200px;
          justify-content: center;
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-icon {
          font-size: 1.25rem;
        }

        .btn-success {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
        }

        .btn-success:hover:not(:disabled) {
          box-shadow: 0 8px 16px -4px rgba(16, 185, 129, 0.4);
          transform: translateY(-2px);
        }

        .btn-danger {
          background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
          color: white;
        }

        .btn-danger:hover {
          box-shadow: 0 8px 16px -4px rgba(239, 68, 68, 0.4);
          transform: translateY(-2px);
        }

        .btn-primary {
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
        }

        .btn-primary:hover {
          box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.4);
          transform: translateY(-2px);
        }

        .btn-highlight {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }

        .btn-highlight:hover {
          box-shadow: 0 8px 16px -4px rgba(245, 158, 11, 0.4);
          transform: translateY(-2px);
        }

        .btn-secondary {
          background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
          color: white;
        }

        .btn-secondary:hover {
          box-shadow: 0 8px 16px -4px rgba(107, 114, 128, 0.4);
          transform: translateY(-2px);
        }

        @media (max-width: 768px) {
          .button-row {
            flex-direction: column;
          }

          .btn {
            flex: none;
            width: 100%;
            min-width: unset;
          }
        }
      `}</style>
    </div>
  );
};
