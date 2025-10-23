// Error Category Component - Updated for Pagination
// Based on index4.html:490-539, 2682-2757

import React, { useState, useEffect } from 'react';
import { ErrorCategory as ErrorCategoryType, Correction, CategoryMetadata, PaginatedErrorData, ErrorGroup as ErrorGroupType } from '../../types/validation';
import { ErrorGroup } from './ErrorGroup';
import { downloadCategoryCSV } from '../../utils/csv';
import { validationService } from '../../services/validation';
import { Pagination } from './Pagination';

interface ErrorCategoryProps {
  category?: ErrorCategoryType; // Optional for backward compatibility
  categoryMetadata?: CategoryMetadata; // For paginated mode
  projectId?: string; // Required for paginated mode
  columnOrder: string[];
  rowsData?: Record<number, any>; // Legacy mode only
  onCorrection: (correction: Correction) => void;
  usePagination?: boolean; // Toggle between legacy and paginated mode
}

export const ErrorCategory: React.FC<ErrorCategoryProps> = ({
  category,
  categoryMetadata,
  projectId,
  columnOrder,
  rowsData = {},
  onCorrection,
  usePagination = false
}) => {
  // State for pagination
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [paginatedData, setPaginatedData] = useState<PaginatedErrorData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Determine category name and metadata
  const categoryName = category?.name || categoryMetadata?.name || 'Unknown';
  const totalPages = categoryMetadata?.total_pages || 1;
  const isSequenceCategory = categoryName.toLowerCase().includes('sequence');

  // Calculate total errors
  const totalErrors = usePagination
    ? (categoryMetadata?.total_errors || 0)
    : (category?.errors.reduce((sum, errorGroup) => {
        const errorCount = errorGroup.rows.length;
        return sum + (isSequenceCategory ? Math.ceil(errorCount / 4) : errorCount);
      }, 0) || 0);

  // Load paginated data when expanded
  useEffect(() => {
    if (usePagination && isExpanded && projectId && categoryName) {
      loadPage(currentPage);
    }
  }, [isExpanded, currentPage, usePagination, projectId, categoryName]);

  const loadPage = async (page: number) => {
    if (!projectId || !categoryName) return;

    setIsLoading(true);
    setError(null);

    try {
      console.log(`[ERROR CATEGORY] Loading ${categoryName} page ${page}...`);
      const data = await validationService.fetchCategoryPage(projectId, categoryName, page);
      setPaginatedData(data);
      console.log(`[ERROR CATEGORY] Loaded ${categoryName} page ${page}:`, {
        errorsOnPage: data.errors_on_page,
        totalPages: data.total_pages
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load page';
      console.error(`[ERROR CATEGORY] Error loading page:`, err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleDownloadCategory = (e: React.MouseEvent) => {
    e.stopPropagation();

    if (usePagination && paginatedData) {
      // For paginated mode, download current page only
      // TODO: Implement full category download across all pages
      downloadCategoryCSV(categoryName, paginatedData.error_groups, paginatedData.rows_data);
    } else if (category) {
      // Legacy mode
      downloadCategoryCSV(categoryName, category.errors, rowsData);
    }
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  // Determine which data to render
  const errorGroups: ErrorGroupType[] = usePagination
    ? (paginatedData?.error_groups || [])
    : (category?.errors || []);

  const currentRowsData = usePagination
    ? (paginatedData?.rows_data || {})
    : rowsData;

  return (
    <div className="error-category">
      <div className="category-header" onClick={toggleExpand}>
        <div className="category-info">
          <span className="category-icon">{isExpanded ? '📂' : '📁'}</span>
          <h4 className="category-name">{categoryName}</h4>
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
          {/* Pagination controls at top */}
          {usePagination && totalPages > 1 && (
            <div className="pagination-container">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
                disabled={isLoading}
              />
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
              <button onClick={() => loadPage(currentPage)} className="retry-btn">
                Retry
              </button>
            </div>
          )}

          {/* Loading state */}
          {isLoading && (
            <div className="loading-message">
              <div className="spinner"></div>
              <p>Loading page {currentPage}...</p>
            </div>
          )}

          {/* Error groups */}
          {!isLoading && !error && errorGroups.length > 0 && (
            <>
              {errorGroups.map((errorGroup, index) => (
                <ErrorGroup
                  key={`${categoryName}-${errorGroup.reason}-${index}`}
                  errorGroup={errorGroup}
                  categoryName={categoryName}
                  columnOrder={columnOrder}
                  rowsData={currentRowsData}
                  onCorrection={onCorrection}
                />
              ))}

              {/* Pagination controls */}
              {usePagination && totalPages > 1 && (
                <div className="pagination-container">
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                    disabled={isLoading}
                  />
                </div>
              )}
            </>
          )}

          {/* Empty state */}
          {!isLoading && !error && errorGroups.length === 0 && (
            <div className="empty-message">
              <p>No errors found in this category.</p>
            </div>
          )}
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

        .page-info {
          color: #64748b;
          font-size: 0.75rem;
          font-weight: 500;
          margin-left: 0.5rem;
        }

        .error-message {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 2rem;
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 0.5rem;
          text-align: center;
        }

        .error-icon {
          font-size: 2rem;
        }

        .error-message p {
          color: #991b1b;
          margin: 0;
        }

        .retry-btn {
          padding: 0.5rem 1rem;
          background: #dc2626;
          color: white;
          border: none;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .retry-btn:hover {
          background: #b91c1c;
        }

        .loading-message {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 3rem;
          text-align: center;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #e2e8f0;
          border-top-color: #6366f1;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .loading-message p {
          color: #64748b;
          margin: 0;
        }

        .pagination-container {
          margin-top: 0;
          margin-bottom: 1.5rem;
          padding: 1rem;
          background: white;
          border-radius: 0.5rem;
          border: 1px solid #e2e8f0;
        }

        .empty-message {
          padding: 3rem;
          text-align: center;
          color: #64748b;
        }

        .empty-message p {
          margin: 0;
        }
      `}</style>
    </div>
  );
};
