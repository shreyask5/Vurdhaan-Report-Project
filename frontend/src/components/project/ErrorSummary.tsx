// Error Summary Component
// Based on index4.html:441-488, 2603-2648

import React from 'react';
import { ErrorData } from '../../types/validation';

interface ErrorSummaryProps {
  errorData: ErrorData;
}

export const ErrorSummary: React.FC<ErrorSummaryProps> = ({ errorData }) => {
  // Use summary data from backend if available, otherwise calculate
  const totalErrors = errorData.summary?.total_errors || errorData.categories.reduce((sum, category) =>
    sum + category.errors.reduce((catSum, errorGroup) =>
      catSum + errorGroup.rows.length, 0), 0);

  const affectedRows = errorData.summary?.error_rows || (() => {
    const errorRows = new Set<number>();
    errorData.categories.forEach(category => {
      category.errors.forEach(errorGroup => {
        errorGroup.rows.forEach(rowError => {
          if (!rowError.file_level) {
            errorRows.add(rowError.row_idx);
          }
        });
      });
    });
    return errorRows.size;
  })();

  const categoryCount = errorData.categories.length;

  return (
    <div className="error-summary">
      <div className="summary-header">
        <h3 className="summary-title">
          ⚠️ Validation Errors Detected
        </h3>
        <p className="summary-subtitle">
          Please review and correct the errors below before proceeding
        </p>
      </div>

      <div className="summary-stats">
        <div className="stat-card error-count">
          <div className="stat-icon">🔴</div>
          <div className="stat-content">
            <div className="stat-value">{totalErrors}</div>
            <div className="stat-label">Total Errors</div>
          </div>
        </div>

        <div className="stat-card row-count">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <div className="stat-value">{affectedRows}</div>
            <div className="stat-label">Affected Rows</div>
          </div>
        </div>

        <div className="stat-card category-count">
          <div className="stat-icon">📂</div>
          <div className="stat-content">
            <div className="stat-value">{categoryCount}</div>
            <div className="stat-label">Error Categories</div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .error-summary {
          background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
          border: 2px solid #fca5a5;
          border-radius: 1rem;
          padding: 2rem;
          margin-bottom: 2rem;
        }

        .summary-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .summary-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: #991b1b;
          margin: 0 0 0.5rem 0;
        }

        .summary-subtitle {
          font-size: 0.875rem;
          color: #7f1d1d;
          margin: 0;
        }

        .summary-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }

        .stat-card {
          background: white;
          border-radius: 0.75rem;
          padding: 1.5rem;
          display: flex;
          align-items: center;
          gap: 1rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          transition: transform 0.2s ease;
        }

        .stat-card:hover {
          transform: translateY(-2px);
        }

        .stat-icon {
          font-size: 2rem;
          filter: grayscale(0.2);
        }

        .stat-content {
          flex: 1;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 700;
          line-height: 1;
          margin-bottom: 0.25rem;
        }

        .stat-label {
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #64748b;
        }

        .error-count .stat-value {
          color: #dc2626;
        }

        .row-count .stat-value {
          color: #ea580c;
        }

        .category-count .stat-value {
          color: #d97706;
        }
      `}</style>
    </div>
  );
};
