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
    <div className="bg-gradient-to-br from-red-50 to-red-100 border-2 border-error-light rounded-xl p-8 mb-8">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-red-800 mb-2">
          ⚠️ Validation Errors Detected
        </h3>
        <p className="text-sm text-red-900">
          Please review and correct the errors below before proceeding
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card rounded-xl p-6 flex items-center gap-4 shadow-card hover:-translate-y-0.5 transition-transform">
          <div className="text-3xl">🔴</div>
          <div className="flex-1">
            <div className="text-3xl font-bold text-error leading-none mb-1">{totalErrors}</div>
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Total Errors</div>
          </div>
        </div>

        <div className="bg-card rounded-xl p-6 flex items-center gap-4 shadow-card hover:-translate-y-0.5 transition-transform">
          <div className="text-3xl">📋</div>
          <div className="flex-1">
            <div className="text-3xl font-bold text-orange-600 leading-none mb-1">{affectedRows}</div>
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Affected Rows</div>
          </div>
        </div>

        <div className="bg-card rounded-xl p-6 flex items-center gap-4 shadow-card hover:-translate-y-0.5 transition-transform">
          <div className="text-3xl">📂</div>
          <div className="flex-1">
            <div className="text-3xl font-bold text-warning leading-none mb-1">{categoryCount}</div>
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Error Categories</div>
          </div>
        </div>
      </div>
    </div>
  );
};
