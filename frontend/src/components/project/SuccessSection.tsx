// Success Section Component
// From index4.html:1291-1311

import React from 'react';

interface SuccessSectionProps {
  onGenerateReport: () => void;
  onDownloadClean: () => void;
  onRevalidate: () => void;
}

export const SuccessSection: React.FC<SuccessSectionProps> = ({
  onGenerateReport,
  onDownloadClean,
  onRevalidate
}) => {
  return (
    <div className="success-section">
      <div className="success-icon">✓</div>
      <h2>Validation Complete!</h2>
      <p>Your CSV file has been successfully validated.</p>

      <div className="action-buttons-container">
        <div className="button-row">
          <button className="btn btn-primary btn-large" onClick={onGenerateReport}>
            <span className="btn-icon">📊</span> Generate CORSIA Report
          </button>
        </div>

        <div className="button-row">
          <button className="btn btn-success" onClick={onDownloadClean}>
            <span className="btn-icon">📥</span> Download Clean Data CSV
          </button>
          <button className="btn btn-secondary" onClick={onRevalidate}>
            <span className="btn-icon">🔄</span> Re-Validate & Process Again
          </button>
        </div>
      </div>

      <style jsx>{`
        .success-section {
          background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
          border: 2px solid #6ee7b7;
          border-radius: 1rem;
          padding: 3rem 2rem;
          text-align: center;
          margin: 2rem 0;
        }

        .success-icon {
          width: 80px;
          height: 80px;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 3rem;
          font-weight: 700;
          margin: 0 auto 1.5rem;
          box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.3);
          animation: successPulse 2s ease-in-out infinite;
        }

        @keyframes successPulse {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.05);
          }
        }

        h2 {
          font-size: 2rem;
          font-weight: 700;
          color: #065f46;
          margin: 0 0 0.5rem 0;
        }

        p {
          font-size: 1rem;
          color: #047857;
          margin: 0 0 2rem 0;
        }

        .action-buttons-container {
          max-width: 800px;
          margin: 0 auto;
        }

        .button-row {
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
          justify-content: center;
        }

        .button-row:last-child {
          margin-bottom: 0;
        }

        .btn {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.875rem 1.75rem;
          border: none;
          border-radius: 0.5rem;
          font-size: 0.9375rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          flex: 1;
          justify-content: center;
          min-width: 200px;
        }

        .btn-icon {
          font-size: 1.25rem;
        }

        .btn-large {
          padding: 1.25rem 2rem;
          font-size: 1.0625rem;
        }

        .btn-primary {
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
        }

        .btn-primary:hover {
          box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.4);
          transform: translateY(-2px);
        }

        .btn-success {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
        }

        .btn-success:hover {
          box-shadow: 0 8px 16px -4px rgba(16, 185, 129, 0.4);
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
