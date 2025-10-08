// Sequence Error Table Component
// Based on index4.html:2372-2495, 1630-1668

import React from 'react';
import { ErrorGroup, Correction } from '../../types/validation';
import { EditableErrorCell } from './EditableErrorCell';
import { downloadCSV } from '../../utils/csv';
import { parseErrorSequence, processSequenceGroups } from '../../utils/validation';

interface SequenceErrorTableProps {
  errorGroup: ErrorGroup;
  columnOrder: string[];
  onCorrection: (correction: Correction) => void;
}

export const SequenceErrorTable: React.FC<SequenceErrorTableProps> = ({
  errorGroup,
  columnOrder,
  onCorrection
}) => {
  // Process sequence groups
  const { groups, highlightMap } = processSequenceGroups(errorGroup);

  const handleDownloadSequence = (groupRows: any[], sequenceKey: string) => {
    const sequenceData = groupRows.map(({ rowError }) => ({
      'Row Index': rowError.row_idx,
      ...rowError.columns,
      'Error Details': rowError.cell_data
    }));

    const filename = `sequence_${sequenceKey.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30)}.csv`;
    downloadCSV(sequenceData, filename);
  };

  return (
    <div className="sequence-error-container">
      {Array.from(groups.entries()).map(([sequenceKey, groupRows], groupIndex) => {
        // Sort by row_idx
        const sortedRows = [...groupRows].sort((a, b) => a.rowError.row_idx - b.rowError.row_idx);
        const sequence = parseErrorSequence(sequenceKey);

        return (
          <div key={`${sequenceKey}-${groupIndex}`} className="sequence-group">
            {/* Header */}
            <div className="sequence-header">
              <span className="sequence-title">
                Sequence Error: {sequence?.errorCode || 'Unknown'}
              </span>
              <button
                onClick={() => handleDownloadSequence(sortedRows, sequenceKey)}
                className="download-btn"
                title="Download sequence as CSV"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7,10 12,15 17,10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                CSV
              </button>
            </div>

            {/* Sequence Table */}
            <div className="table-wrapper">
              <table className="sequence-table">
                <thead>
                  <tr>
                    <th>Row</th>
                    {columnOrder.map(col => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedRows.map(({ rowError, originalIndex }, rowIndex) => {
                    const isHighlighted = highlightMap.get(rowError.row_idx) || false;
                    const isLastInSequence = rowIndex === sortedRows.length - 1;

                    // Determine cells to highlight (red for mismatched Destination/Origin)
                    const nextRow = sortedRows[rowIndex + 1];
                    const nextOriginICAO = nextRow?.rowError.columns['Origin ICAO'];
                    const currentDestICAO = rowError.columns['Destination ICAO'];

                    return (
                      <tr
                        key={rowError.row_idx}
                        className={`${isHighlighted ? 'sequence-error-row' : ''} ${isLastInSequence ? 'last-in-sequence' : ''}`}
                      >
                        <td className="row-index-cell">{rowError.row_idx}</td>
                        {columnOrder.map(col => {
                          // Check if this cell should be red-highlighted
                          const shouldHighlight =
                            col === 'Destination ICAO' &&
                            nextOriginICAO !== undefined &&
                            currentDestICAO !== nextOriginICAO;

                          // Destination and Origin ICAO are not editable in sequence tables
                          const isEditable = errorGroup.columns.includes(col) &&
                                            col !== 'Destination ICAO' &&
                                            col !== 'Origin ICAO';

                          return (
                            <td key={col} className={shouldHighlight ? 'red-highlight' : ''}>
                              {isEditable ? (
                                <input
                                  type="text"
                                  defaultValue={rowError.columns[col] || ''}
                                  onChange={(e) => onCorrection({
                                    row_idx: rowError.row_idx,
                                    column: col,
                                    old_value: rowError.columns[col],
                                    new_value: e.target.value
                                  })}
                                  className="cell-input"
                                />
                              ) : (
                                <span>{rowError.columns[col] !== null && rowError.columns[col] !== undefined ? String(rowError.columns[col]) : ''}</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Sequence Summary */}
            <div className="sequence-summary">
              <strong>Sequence Summary:</strong> {sortedRows.length} consecutive flights
              {sequence && (
                <> - Expected: {sequence.destinationICAO} → {sequence.originICAO}</>
              )}
            </div>
          </div>
        );
      })}

      <style jsx>{`
        .sequence-error-container {
          margin-bottom: 1rem;
        }

        .sequence-group {
          background: white;
          border: 2px solid #fca5a5;
          border-radius: 0.5rem;
          margin-bottom: 1.5rem;
          overflow: hidden;
        }

        .sequence-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
          border-bottom: 2px solid #fca5a5;
        }

        .sequence-title {
          font-size: 0.875rem;
          font-weight: 700;
          color: #991b1b;
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

        .table-wrapper {
          overflow-x: auto;
          padding: 1rem;
        }

        .sequence-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.75rem;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.375rem;
          overflow: hidden;
        }

        .sequence-table th {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          padding: 0.5rem 0.75rem;
          text-align: center;
          font-weight: 600;
          font-size: 0.625rem;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border-bottom: 2px solid #cbd5e1;
          position: sticky;
          top: 0;
          white-space: nowrap;
        }

        .sequence-table td {
          padding: 0.375rem 0.75rem;
          text-align: center;
          border-bottom: 1px solid #e2e8f0;
          font-size: 0.75rem;
        }

        .row-index-cell {
          font-weight: 600;
          background: #f8fafc;
          color: #475569;
        }

        /* Highlight 2nd and 3rd rows in 4-row sequences */
        .sequence-error-row {
          background: #fef3c7 !important;
        }

        .sequence-error-row td {
          background: #fef3c7;
        }

        /* Red highlight for mismatched cells */
        .red-highlight {
          background: #fee2e2 !important;
          color: #991b1b;
          font-weight: 700;
        }

        /* Last row in sequence gets bottom border */
        .last-in-sequence {
          border-bottom: 3px solid #6366f1;
        }

        .cell-input {
          width: 100%;
          padding: 0.25rem 0.375rem;
          border: 1px solid #cbd5e1;
          border-radius: 0.25rem;
          font-size: 0.75rem;
          text-align: center;
          background: white;
        }

        .cell-input:focus {
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
        }

        .sequence-summary {
          padding: 0.75rem 1rem;
          background: #f8fafc;
          border-top: 1px solid #e2e8f0;
          font-size: 0.75rem;
          color: #475569;
        }
      `}</style>
    </div>
  );
};
