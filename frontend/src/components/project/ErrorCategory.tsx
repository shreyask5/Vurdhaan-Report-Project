// Error Category Component
// Based on index4.html:490-539, 2682-2757

import React, { useState } from 'react';
import { ErrorCategory as ErrorCategoryType, Correction } from '../../types/validation';
import { ErrorGroup } from './ErrorGroup';
import { downloadCSV } from '../../utils/csv';

interface ErrorCategoryProps {
  category: ErrorCategoryType;
  columnOrder: string[];
  onCorrection: (correction: Correction) => void;
}

export const ErrorCategory: React.FC<ErrorCategoryProps> = ({
  category,
  columnOrder,
  onCorrection
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Calculate total errors in this category
  const totalErrors = category.errors.reduce((sum, errorGroup) =>
    sum + errorGroup.rows.length, 0);

  const handleDownloadCategory = (e: React.MouseEvent) => {
    e.stopPropagation();

    // Prepare enriched data with category/reason/details/row index
    const enrichedData: any[] = [];

    category.errors.forEach(errorGroup => {
      errorGroup.rows.forEach(rowError => {
        const rowData: any = {
          Category: category.name,
          Reason: errorGroup.reason,
          'Row Index': rowError.row_idx,
          ...rowError.columns
        };

        // Add cell_data if present
        if (rowError.cell_data) {
          rowData['Error Details'] = rowError.cell_data;
        }

        enrichedData.push(rowData);
      });
    });

    const filename = `errors_${category.name.replace(/\s+/g, '_')}.csv`;
    downloadCSV(enrichedData, filename);
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div className="error-category">
      <div className="category-header" onClick={toggleExpand}>
        <div className="category-info">
          <span className="category-icon">{isExpanded ? '📂' : '📁'}</span>
          <h4 className="category-name">{category.name}</h4>
          <span className="error-badge">{totalErrors} errors</span>
        </div>
        <div className="category-actions" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={handleDownloadCategory}
            className="download-btn"
            title="Download category as CSV"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            CSV
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="category-content">
          {category.errors.map((errorGroup, index) => (
            <ErrorGroup
              key={`${category.name}-${errorGroup.reason}-${index}`}
              errorGroup={errorGroup}
              columnOrder={columnOrder}
              onCorrection={onCorrection}
            />
          ))}
        </div>
      )}

      <style jsx>{`
        .error-category {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.75rem;
          margin-bottom: 1rem;
          overflow: hidden;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .category-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 1.5rem;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .category-header:hover {
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        }

        .category-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex: 1;
        }

        .category-icon {
          font-size: 1.25rem;
        }

        .category-name {
          font-size: 1rem;
          font-weight: 600;
          color: #1e293b;
          margin: 0;
        }

        .error-badge {
          background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
          color: white;
          padding: 0.25rem 0.75rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .category-actions {
          display: flex;
          gap: 0.5rem;
        }

        .download-btn {
          display: flex;
          align-items: center;
          gap: 0.375rem;
          padding: 0.5rem 0.75rem;
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
          border: none;
          border-radius: 0.375rem;
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .download-btn:hover {
          box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
          transform: translateY(-1px);
        }

        .category-content {
          padding: 1.5rem;
          background: #fafbfc;
        }
      `}</style>
    </div>
  );
};
