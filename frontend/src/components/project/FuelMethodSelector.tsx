// Fuel Method Selector Component
// Based on index4.html:1711-1753, 1571-1605

import React from 'react';
import { FuelMethod } from '../../types/validation';

interface FuelMethodSelectorProps {
  onSelect: (method: FuelMethod) => void;
  selectedMethod?: FuelMethod;
}

export const FuelMethodSelector: React.FC<FuelMethodSelectorProps> = ({
  onSelect,
  selectedMethod
}) => {
  const methods: FuelMethod[] = ["Block Off - Block On", "Method B"];

  return (
    <div className="fuel-method-selector">
      <h3 className="text-xl font-semibold mb-4 text-gray-700">
        Select Fuel Calculation Method
      </h3>
      <p className="text-sm text-gray-600 mb-6">
        Choose the method used for fuel consumption calculation in your CSV file
      </p>

      <div className="method-grid">
        {methods.map((method) => (
          <button
            key={method}
            onClick={() => onSelect(method)}
            className={`method-card ${selectedMethod === method ? 'selected' : ''}`}
            type="button"
          >
            <div className="method-icon">
              {method === "Block Off - Block On" ? '⛽' : '📊'}
            </div>
            <h4 className="method-title">{method}</h4>
            <p className="method-description">
              {method === "Block Off - Block On"
                ? 'Uses Block Off Fuel and Block On Fuel for calculations'
                : 'Uses Uplift weight and Remaining Fuel for calculations'}
            </p>
            {selectedMethod === method && (
              <div className="selected-indicator">✓ Selected</div>
            )}
          </button>
        ))}
      </div>

      <style jsx>{`
        .fuel-method-selector {
          margin-bottom: 2rem;
        }

        .method-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 1.5rem;
        }

        .method-card {
          background: white;
          border: 2px solid #e2e8f0;
          border-radius: 1rem;
          padding: 2rem;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
        }

        .method-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, transparent 100%);
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .method-card:hover {
          border-color: #6366f1;
          transform: translateY(-4px);
          box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.2);
        }

        .method-card:hover::before {
          opacity: 1;
        }

        .method-card.selected {
          border-color: #4f46e5;
          background: linear-gradient(135deg, #eef2ff 0%, white 100%);
          box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.3);
        }

        .method-card.selected::before {
          opacity: 1;
        }

        .method-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
          filter: grayscale(0.3);
        }

        .method-card.selected .method-icon {
          filter: grayscale(0);
          transform: scale(1.1);
          transition: transform 0.3s ease;
        }

        .method-title {
          font-size: 1.1rem;
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 0.5rem;
        }

        .method-description {
          font-size: 0.875rem;
          color: #64748b;
          line-height: 1.5;
          margin: 0;
        }

        .selected-indicator {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          padding: 0.25rem 0.75rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 600;
          box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
        }
      `}</style>
    </div>
  );
};
