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

  // TEMPORARY DEBUG: Log first few cells
  React.useEffect(() => {
    if (rowIdx === 11 && column === 'Date') {
      console.log('[EDITABLE CELL DEBUG]', {
        rowIdx,
        column,
        value,
        valueType: typeof value,
        isEditable,
        currentValue
      });
    }
  }, [rowIdx, column, value, isEditable, currentValue]);

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
    </td>
  );
};
