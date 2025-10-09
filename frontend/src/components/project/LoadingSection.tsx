// Loading Section Component
// From index4.html loading section and spinner

import React from 'react';

interface LoadingSectionProps {
  message?: string;
  progress?: number; // 0-100
}

export const LoadingSection: React.FC<LoadingSectionProps> = ({
  message = 'Processing...',
  progress
}) => {
  return (
    <div className="loading-section">
      <div className="spinner"></div>
      <h3 className="loading-message">{message}</h3>
      {progress !== undefined && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }}></div>
        </div>
      )}

      <style jsx>{`
        .loading-section {
          background: white;
          border-radius: 1rem;
          padding: 4rem 2rem;
          text-align: center;
          margin: 2rem 0;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .spinner {
          width: 60px;
          height: 60px;
          margin: 0 auto 1.5rem;
          border: 4px solid #e2e8f0;
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .loading-message {
          font-size: 1.25rem;
          font-weight: 600;
          color: #475569;
          margin: 0 0 1.5rem 0;
        }

        .progress-bar {
          width: 100%;
          max-width: 500px;
          height: 8px;
          background: #e2e8f0;
          border-radius: 9999px;
          overflow: hidden;
          margin: 0 auto;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
          border-radius: 9999px;
          transition: width 0.3s ease;
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% {
            opacity: 0.6;
          }
          50% {
            opacity: 1;
          }
          100% {
            opacity: 0.6;
          }
        }
      `}</style>
    </div>
  );
};
