// Validation Parameters Form Component
// Based on index4.html:1204-1237

import React, { useState } from 'react';
import { ValidationParams, DateFormat } from '../../types/validation';

interface ValidationFormProps {
  onSubmit: (params: ValidationParams) => void;
  onBack?: () => void;
}

export const ValidationForm: React.FC<ValidationFormProps> = ({
  onSubmit,
  onBack
}) => {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 6 }, (_, i) => (currentYear - 5 + i).toString());

  const [params, setParams] = useState<ValidationParams>({
    monitoring_year: currentYear.toString(),
    date_format: 'DMY',
    flight_starts_with: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(params);
  };

  const handleChange = (field: keyof ValidationParams, value: string) => {
    setParams(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="validation-form-container">
      <div className="form-header">
        <h3 className="text-xl font-semibold text-gray-700">
          Validation Parameters
        </h3>
        <p className="text-sm text-gray-600 mt-2">
          Configure validation settings for your flight data
        </p>
      </div>

      <form onSubmit={handleSubmit} className="validation-form">
        {/* Monitoring Year */}
        <div className="form-group">
          <label htmlFor="monitoring_year" className="form-label">
            Monitoring Year *
          </label>
          <select
            id="monitoring_year"
            value={params.monitoring_year}
            onChange={(e) => handleChange('monitoring_year', e.target.value)}
            className="form-select"
            required
          >
            {years.map(year => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
          <p className="form-help">
            Select the year for which you're monitoring flight data
          </p>
        </div>

        {/* Date Format */}
        <div className="form-group">
          <label htmlFor="date_format" className="form-label">
            Date Format *
          </label>
          <select
            id="date_format"
            value={params.date_format}
            onChange={(e) => handleChange('date_format', e.target.value as DateFormat)}
            className="form-select"
            required
          >
            <option value="DMY">DD/MM/YYYY</option>
            <option value="MDY">MM/DD/YYYY</option>
          </select>
          <p className="form-help">
            Choose the date format used in your CSV file
          </p>
        </div>

        {/* Flight Starts With */}
        <div className="form-group">
          <label htmlFor="flight_starts_with" className="form-label">
            Flight Number Prefix
          </label>
          <input
            id="flight_starts_with"
            type="text"
            value={params.flight_starts_with}
            onChange={(e) => handleChange('flight_starts_with', e.target.value)}
            className="form-input"
            placeholder="e.g., AI, BA, UA"
          />
          <p className="form-help">
            Optional: Enter the prefix that all flight numbers should start with
          </p>
        </div>

        {/* Action Buttons */}
        <div className="form-actions">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="btn-secondary"
            >
              ← Back
            </button>
          )}
          <button
            type="submit"
            className="btn-primary"
          >
            Submit & Validate
          </button>
        </div>
      </form>

      <style jsx>{`
        .validation-form-container {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 1rem;
          padding: 2rem;
          margin-bottom: 2rem;
        }

        .form-header {
          margin-bottom: 2rem;
        }

        .validation-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-label {
          font-size: 0.875rem;
          font-weight: 600;
          color: #374151;
        }

        .form-select,
        .form-input {
          padding: 0.75rem 1rem;
          border: 2px solid #cbd5e1;
          border-radius: 0.5rem;
          font-size: 0.875rem;
          color: #1e293b;
          background: white;
          transition: all 0.2s ease;
        }

        .form-select:focus,
        .form-input:focus {
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .form-help {
          font-size: 0.75rem;
          color: #64748b;
          margin: 0;
        }

        .form-actions {
          display: flex;
          gap: 1rem;
          margin-top: 1rem;
        }

        .btn-primary,
        .btn-secondary {
          padding: 0.875rem 1.75rem;
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

        .btn-primary:hover {
          box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
          transform: translateY(-2px);
        }

        .btn-secondary {
          background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
          color: white;
        }

        .btn-secondary:hover {
          box-shadow: 0 10px 15px -3px rgba(100, 116, 139, 0.3);
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
};
