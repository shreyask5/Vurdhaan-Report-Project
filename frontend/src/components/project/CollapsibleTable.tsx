// Collapsible Table Component for Chat Query Results
// Based on chat.js:289-385

import React, { useState, useRef, useEffect } from 'react';
import { downloadCSV } from '../../utils/csv';

interface CollapsibleTableProps {
  data: any[];
  filename?: string;
}

export const CollapsibleTable: React.FC<CollapsibleTableProps> = ({
  data,
  filename = 'query_results.csv'
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    downloadCSV(data, filename);
  };

  // Auto-scroll into view when expanded
  useEffect(() => {
    if (isExpanded && contentRef.current) {
      contentRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isExpanded]);

  if (!data || data.length === 0) {
    return null;
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="collapsible-table">
      <div className="table-header" onClick={handleToggle}>
        <div className="header-left">
          <div className="header-title">Query Results</div>
          <div className="header-info">{data.length} rows</div>
        </div>
        <div className="header-right">
          <button
            onClick={handleDownload}
            className="download-btn"
            title="Download as CSV"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            CSV
          </button>
          <div className={`toggle-icon ${isExpanded ? 'expanded' : ''}`}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </div>
      </div>

      <div
        ref={contentRef}
        className={`table-content ${isExpanded ? 'expanded' : ''}`}
      >
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map(col => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={index}>
                  {columns.map(col => (
                    <td key={col}>{row[col] !== null && row[col] !== undefined ? String(row[col]) : ''}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <style jsx>{`
        .collapsible-table {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 0.75rem;
          overflow: hidden;
          margin-top: 1rem;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .table-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 1.25rem;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          cursor: pointer;
          transition: all 0.2s ease;
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .table-header:hover {
          background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .header-title {
          font-weight: 600;
          color: #1e293b;
          font-size: 0.875rem;
        }

        .header-info {
          color: #64748b;
          font-size: 0.75rem;
          padding: 0.25rem 0.625rem;
          background: white;
          border-radius: 9999px;
          border: 1px solid #cbd5e1;
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .download-btn {
          display: flex;
          align-items: center;
          gap: 0.375rem;
          padding: 0.5rem 0.875rem;
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

        .toggle-icon {
          color: #64748b;
          transition: transform 0.3s ease;
          display: flex;
          align-items: center;
        }

        .toggle-icon.expanded {
          transform: rotate(180deg);
        }

        .table-content {
          max-height: 0;
          overflow: hidden;
          transition: max-height 0.3s ease;
        }

        .table-content.expanded {
          max-height: 600px;
          overflow-y: auto;
        }

        .table-wrapper {
          padding: 1rem;
        }

        .data-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.8125rem;
        }

        .data-table thead {
          position: sticky;
          top: 0;
          background: white;
          z-index: 5;
        }

        .data-table th {
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          padding: 0.75rem 1rem;
          text-align: left;
          font-weight: 600;
          font-size: 0.75rem;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border-bottom: 2px solid #cbd5e1;
          white-space: nowrap;
        }

        .data-table td {
          padding: 0.75rem 1rem;
          border-bottom: 1px solid #e2e8f0;
          color: #1e293b;
        }

        .data-table tbody tr:hover {
          background: #f8fafc;
        }

        /* Custom scrollbar */
        .table-content::-webkit-scrollbar {
          width: 8px;
        }

        .table-content::-webkit-scrollbar-track {
          background: #f1f5f9;
        }

        .table-content::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }

        .table-content::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  );
};
