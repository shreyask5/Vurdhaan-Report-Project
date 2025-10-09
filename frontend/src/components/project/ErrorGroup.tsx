// Error Group Component
// Based on index4.html:541-584, 2759-2839, 2497-2601

import React, { useState } from 'react';
import { ErrorGroup as ErrorGroupType, Correction } from '../../types/validation';
import { EditableErrorCell } from './EditableErrorCell';
import { SequenceErrorTable } from './SequenceErrorTable';
import { downloadReasonGroupCSV } from '../../utils/csv';
import { parseErrorSequence } from '../../utils/errorProcessing';

interface ErrorGroupProps {
  errorGroup: ErrorGroupType;
  categoryName: string;
  columnOrder: string[];
  rowsData?: Record<number, any>;
  onCorrection: (correction: Correction) => void;
}

export const ErrorGroup: React.FC<ErrorGroupProps> = ({
  errorGroup,
  categoryName,
  columnOrder,
  rowsData = {},
  onCorrection
}) => {
  const [displayedRows, setDisplayedRows] = useState(100); // Initial batch size

  // Debug logging
  React.useEffect(() => {
    console.log('[ERROR GROUP] Rendering:', {
      reason: errorGroup.reason,
      rowCount: errorGroup.rows.length,
      columnOrderLength: columnOrder.length,
      columnOrder,
      firstRow: errorGroup.rows[0],
      rowsDataKeys: Object.keys(rowsData).length
    });
  }, [errorGroup, columnOrder, rowsData]);

  // Check if this is a sequence error group
  const isSequenceError = errorGroup.rows.some(row => parseErrorSequence(row.cell_data) !== null);

  const handleDownloadGroup = (e: React.MouseEvent) => {
    e.stopPropagation();
    downloadReasonGroupCSV(categoryName, errorGroup, rowsData);
  };

  const loadMoreRows = () => {
    setDisplayedRows(prev => Math.min(prev + 100, errorGroup.rows.length));
  };

  const hasMoreRows = displayedRows < errorGroup.rows.length;

  // If it's a sequence error, use the specialized component
  if (isSequenceError) {
    return (
      <SequenceErrorTable
        errorGroup={errorGroup}
        columnOrder={columnOrder}
        rowsData={rowsData}
        onCorrection={onCorrection}
      />
    );
  }

  // Regular error group rendering
  return (
    <div className="error-group">
      <div className="group-header">
        <div className="group-info">
          <h5 className="group-reason">{errorGroup.reason}</h5>
          <span className="group-count">{errorGroup.rows.length} rows</span>
        </div>
        <button
          onClick={handleDownloadGroup}
          className="download-btn"
          title="Download group as CSV"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          CSV
        </button>
      </div>

      <div className="group-content">
        {/* Render errors in batches - From index4.html:2497-2601 */}
        {errorGroup.rows.slice(0, displayedRows).map((rowError, index) => {
          // Get actual row data from rowsData
          const actualRowData = rowsData[rowError.row_idx] || {};

          // Debug log for first few rows
          if (index < 2) {
            console.log('[ERROR GROUP] Row data:', {
              row_idx: rowError.row_idx,
              actualRowData,
              columns: errorGroup.columns,
              cellData: rowError.cell_data
            });
          }

          return (
            <div key={`${rowError.row_idx}-${index}`} className="error-row">
              <div className="error-details">
                <strong>Row {rowError.row_idx}</strong>
                {rowError.cell_data && (
                  <span className="cell-data"> - {rowError.cell_data}</span>
                )}
              </div>

              {/* One-row table with editable cells */}
              <div className="table-wrapper">
                <table className="error-row-table">
                  <thead>
                    <tr>
                      {columnOrder.map(col => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      {columnOrder.map(col => {
                        const isEditable = errorGroup.columns?.includes(col) || false;
                        const cellValue = actualRowData[col];
                        return (
                          <EditableErrorCell
                            key={col}
                            rowIdx={rowError.row_idx}
                            column={col}
                            value={cellValue}
                            isEditable={isEditable}
                            onChange={onCorrection}
                          />
                        );
                      })}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}

        {/* Load More Button */}
        {hasMoreRows && (
          <button onClick={loadMoreRows} className="load-more-btn">
            Load More ({errorGroup.rows.length - displayedRows} remaining)
          </button>
        )}
      </div>

      <style jsx>{`
        .error-group {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          margin-bottom: 1rem;
          overflow: hidden;
        }

        .group-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
          border-bottom: 1px solid #fbbf24;
        }

        .group-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .group-reason {
          font-size: 0.875rem;
          font-weight: 600;
          color: #92400e;
          margin: 0;
        }

        .group-count {
          background: #f59e0b;
          color: white;
          padding: 0.125rem 0.5rem;
          border-radius: 9999px;
          font-size: 0.625rem;
          font-weight: 600;
        }

        .download-btn {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.375rem 0.625rem;
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
          border: none;
          border-radius: 0.25rem;
          font-size: 0.625rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .download-btn:hover {
          box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
          transform: translateY(-1px);
        }

        .group-content {
          padding: 1rem;
        }

        .error-row {
          margin-bottom: 1rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #f1f5f9;
        }

        .error-row:last-child {
          border-bottom: none;
          margin-bottom: 0;
          padding-bottom: 0;
        }

        .error-details {
          font-size: 0.75rem;
          color: #64748b;
          margin-bottom: 0.5rem;
          padding: 0.5rem;
          background: #f8fafc;
          border-radius: 0.25rem;
        }

        .cell-data {
          color: #dc2626;
          font-weight: 600;
        }

        .table-wrapper {
          overflow-x: auto;
        }

        .error-row-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.75rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          overflow: hidden;
          table-layout: auto;
          min-width: 100%;
        }

        .error-row-table th {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          padding: 0.5rem 0.75rem;
          text-align: center;
          font-weight: 600;
          font-size: 0.625rem;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border-bottom: 2px solid #cbd5e1;
          white-space: nowrap;
          min-width: 100px;
        }

        .error-row-table :global(td) {
          padding: 0.375rem 0.75rem;
          text-align: center;
          border-bottom: 1px solid #e2e8f0;
          min-width: 100px;
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .error-row-table :global(td.table-cell) {
          padding: 0.375rem 0.75rem;
        }

        .error-row-table :global(td.editable) {
          background: #fef3c7;
        }

        .error-row-table :global(input.cell-input) {
          width: 100%;
          min-width: 80px;
        }

        .load-more-btn {
          width: 100%;
          padding: 0.75rem;
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
          border: 2px dashed #cbd5e1;
          border-radius: 0.5rem;
          color: #475569;
          font-weight: 600;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-top: 1rem;
        }

        .load-more-btn:hover {
          background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
          border-color: #94a3b8;
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
};
