// Column Mapping Wizard Component
// Based on index4.html:1784-1955, 1821-1866

import React, { useState, useEffect } from 'react';
import { FuelMethod, ColumnMapping, FUEL_METHOD_COLUMNS, ValidationParams } from '../../types/validation';

interface ColumnMappingWizardProps {
  uploadedColumns: string[];
  fuelMethod: FuelMethod;
  onComplete: (mapping: ColumnMapping) => void;
  onBack?: () => void;
  onSubmit?: () => Promise<void>;
  projectId?: string;
  validationParams?: ValidationParams | null;
}

export const ColumnMappingWizard: React.FC<ColumnMappingWizardProps> = ({
  uploadedColumns,
  fuelMethod,
  onComplete,
  onBack,
  onSubmit,
  projectId,
  validationParams
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [mapping, setMapping] = useState<ColumnMapping>({});

  const requiredColumns = FUEL_METHOD_COLUMNS[fuelMethod];
  const totalSteps = requiredColumns.length;
  const currentRequiredColumn = requiredColumns[currentStep];
  const progress = ((currentStep + 1) / totalSteps) * 100;

  // Get already mapped columns
  const mappedColumns = Object.values(mapping);

  const handleColumnSelect = (csvColumn: string) => {
    const newMapping = { ...mapping, [currentRequiredColumn]: csvColumn };
    setMapping(newMapping);

    // Auto-advance to next step
    if (currentStep < totalSteps - 1) {
      setTimeout(() => setCurrentStep(currentStep + 1), 200);
    }
  };

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      // Unmap the current column before going back
      const previousRequiredColumn = requiredColumns[currentStep];
      const newMapping = { ...mapping };
      delete newMapping[previousRequiredColumn];
      setMapping(newMapping);

      setCurrentStep(currentStep - 1);
    } else if (onBack) {
      // First step and onBack is provided - go back to previous page
      onBack();
    }
  };

  const handleComplete = () => {
    if (Object.keys(mapping).length === totalSteps) {
      onComplete(mapping);
    }
  };

  const handleFinalSubmit = async () => {
    if (!canComplete) {
      console.log('Cannot complete - missing mappings:', {
        totalSteps,
        mappedCount: Object.keys(mapping).length,
        mapping,
        requiredColumns
      });
      return;
    }

    // Complete the mapping first
    onComplete(mapping);

    // If onSubmit is provided, trigger final submission
    if (onSubmit) {
      await onSubmit();
    }
  };

  // Check if all required columns are mapped
  const canComplete = requiredColumns.every(col => mapping[col] !== undefined && mapping[col] !== null && mapping[col] !== '');
  const isOnFirstStep = currentStep === 0;
  const isOnLastStep = currentStep === totalSteps - 1;

  return (
    <div className="column-mapping-wizard">
      {/* Header */}
      <div className="wizard-header">
        <h3 className="text-xl font-semibold text-gray-700">
          Map Your CSV Columns
        </h3>
        <p className="text-sm text-gray-600 mt-2">
          Match each required field to a column in your CSV file
        </p>
      </div>

      {/* Progress Bar - From index4.html:964-1002 */}
      <div className="progress-section">
        <div className="progress-info">
          <span className="text-sm font-semibold text-gray-700">
            Step {currentStep + 1} of {totalSteps}
          </span>
          <span className="text-xs text-gray-500">
            {Math.round(progress)}% Complete
          </span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Current Step */}
      <div className="mapping-step">
        <div className="required-column-display">
          <label className="text-sm font-medium text-gray-600">
            Required Field:
          </label>
          <div className="required-column-name">
            {currentRequiredColumn}
          </div>
        </div>

        {/* Column Selector Grid - From index4.html:1821-1866 */}
        <div className="column-selector">
          <label className="text-sm font-medium text-gray-600 mb-3 block">
            Select matching column from your CSV:
          </label>
          <div className="column-grid">
            {uploadedColumns.map((column) => {
              const isSelected = mapping[currentRequiredColumn] === column;
              // A column is "already mapped" only if it's mapped to a DIFFERENT required field
              // This allows users to re-select when going back to change their mapping
              const isAlreadyMapped = Object.entries(mapping).some(
                ([requiredCol, csvCol]) =>
                  csvCol === column && requiredCol !== currentRequiredColumn
              );

              return (
                <button
                  key={column}
                  onClick={() => !isAlreadyMapped && handleColumnSelect(column)}
                  disabled={isAlreadyMapped}
                  className={`column-btn ${isSelected ? 'selected' : ''} ${
                    isAlreadyMapped ? 'disabled' : ''
                  }`}
                  type="button"
                >
                  {column}
                  {isSelected && <span className="checkmark">✓</span>}
                  {isAlreadyMapped && <span className="mapped-indicator">Mapped</span>}
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation Buttons - From index4.html:1881-1908 */}
        <div className="wizard-navigation">
          <button
            onClick={handlePrevious}
            disabled={isOnFirstStep && !onBack}
            className="btn-secondary"
            type="button"
          >
            ← {isOnFirstStep ? 'Back to Upload' : 'Previous'}
          </button>

          {!isOnLastStep ? (
            <button
              onClick={handleNext}
              disabled={!mapping[currentRequiredColumn]}
              className="btn-primary"
              type="button"
            >
              Next →
            </button>
          ) : onSubmit ? (
            <button
              onClick={handleFinalSubmit}
              disabled={!canComplete}
              className="btn-success"
              type="button"
            >
              Submit & Validate
            </button>
          ) : (
            <button
              onClick={handleComplete}
              disabled={!canComplete}
              className="btn-success"
              type="button"
            >
              Complete Mapping
            </button>
          )}
        </div>
      </div>

      <style jsx>{`
        .column-mapping-wizard {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 1rem;
          padding: 2rem;
          margin-bottom: 2rem;
        }

        .wizard-header {
          margin-bottom: 2rem;
        }

        .progress-section {
          margin-bottom: 2rem;
        }

        .progress-info {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }

        .progress-bar {
          height: 8px;
          background: #e2e8f0;
          border-radius: 9999px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
          transition: width 0.3s ease;
          border-radius: 9999px;
        }

        .mapping-step {
          margin-bottom: 1.5rem;
        }

        .required-column-display {
          background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
          border: 2px solid #c7d2fe;
          border-radius: 0.75rem;
          padding: 1.5rem;
          margin-bottom: 2rem;
          text-align: center;
        }

        .required-column-name {
          font-size: 1.5rem;
          font-weight: 700;
          color: #4f46e5;
          margin-top: 0.5rem;
        }

        .column-selector {
          margin-bottom: 2rem;
        }

        .column-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 0.75rem;
        }

        .column-btn {
          background: white;
          border: 2px solid #cbd5e1;
          border-radius: 0.5rem;
          padding: 0.75rem 1rem;
          font-size: 0.875rem;
          font-weight: 500;
          color: #475569;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
          text-align: left;
        }

        .column-btn:hover:not(.disabled) {
          border-color: #6366f1;
          background: #f8fafc;
          transform: translateY(-2px);
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .column-btn.selected {
          border-color: #4f46e5;
          background: linear-gradient(135deg, #eef2ff 0%, white 100%);
          color: #4f46e5;
          font-weight: 600;
        }

        .column-btn.disabled {
          background: #f1f5f9;
          border-color: #e2e8f0;
          color: #94a3b8;
          cursor: not-allowed;
          opacity: 0.6;
        }

        .checkmark {
          position: absolute;
          top: 0.5rem;
          right: 0.5rem;
          color: #10b981;
          font-weight: bold;
        }

        .mapped-indicator {
          position: absolute;
          top: 0.5rem;
          right: 0.5rem;
          font-size: 0.625rem;
          color: #64748b;
          background: #e2e8f0;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
        }

        .wizard-navigation {
          display: flex;
          gap: 1rem;
          justify-content: space-between;
        }

        .btn-primary,
        .btn-secondary,
        .btn-success {
          padding: 0.75rem 1.5rem;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s ease;
          border: none;
          flex: 1;
        }

        .btn-primary {
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
          transform: translateY(-2px);
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
          color: white;
        }

        .btn-secondary:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(100, 116, 139, 0.3);
          transform: translateY(-2px);
        }

        .btn-secondary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-success {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
        }

        .btn-success:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
          transform: translateY(-2px);
        }

        .btn-success:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};
