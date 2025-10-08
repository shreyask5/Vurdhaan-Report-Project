// Editable Error Cell Component
// Based on index4.html:789-820, 3181-3199

import React, { useState, useEffect } from 'react';
import { Correction } from '../../types/validation';

interface EditableErrorCellProps {
  rowIdx: number;
  column: string;
  value: any;
  isEditable: boolean;
  onChange: (correction: Correction) => void;
}

export const EditableErrorCell: React.FC<EditableErrorCellProps> = ({
  rowIdx,
  column,
  value,
  isEditable,
  onChange
}) => {
  const [currentValue, setCurrentValue] = useState(value);
  const [isFocused, setIsFocused] = useState(false);
  const originalValue = value;

  useEffect(() => {
    setCurrentValue(value);
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setCurrentValue(newValue);

    // Notify parent of correction
    onChange({
      row_idx: rowIdx,
      column: column,
      old_value: originalValue,
      new_value: newValue
    });
  };

  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  if (!isEditable) {
    return (
      <td className="table-cell">
        {value !== null && value !== undefined ? String(value) : ''}
        <style jsx>{`
          .table-cell {
            padding: 0.375rem 0.75rem;
            font-size: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
            text-align: center;
          }
        `}</style>
      </td>
    );
  }

  const hasChanged = currentValue !== originalValue;

  return (
    <td className={`table-cell editable ${isFocused ? 'focused' : ''} ${hasChanged ? 'changed' : ''}`}>
      <input
        type="text"
        value={currentValue !== null && currentValue !== undefined ? String(currentValue) : ''}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className="cell-input"
      />
      <style jsx>{`
        .table-cell {
          padding: 0.25rem;
          font-size: 0.75rem;
          border-bottom: 1px solid #e2e8f0;
          text-align: center;
          background: white;
          transition: background-color 0.2s ease;
        }

        .table-cell.editable {
          background: #fef3c7;
        }

        .table-cell.editable.focused {
          background: #fde68a;
        }

        .table-cell.editable.changed {
          background: #bfdbfe;
        }

        .cell-input {
          width: 100%;
          padding: 0.375rem 0.5rem;
          border: 1px solid transparent;
          border-radius: 0.25rem;
          font-size: 0.75rem;
          text-align: center;
          background: transparent;
          transition: all 0.2s ease;
        }

        .cell-input:focus {
          outline: none;
          border-color: #6366f1;
          background: white;
        }

        .editable.changed .cell-input {
          font-weight: 600;
          color: #1e40af;
        }
      `}</style>
    </td>
  );
};
