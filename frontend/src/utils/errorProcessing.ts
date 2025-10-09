// Error Processing Utilities
// Converted from index4.html JavaScript functions

import { ErrorGroup, SequenceError } from '../types/validation';

/**
 * Parse error sequence from cell_data string
 * Pattern: "ERRORCODE : ICAO1 → ICAO2"
 * Example: "TCCOH : LTAF → LTAI"
 */
export function parseErrorSequence(cellData?: string): SequenceError | null {
  if (!cellData || typeof cellData !== 'string') {
    return null;
  }

  // Match pattern like "TCCOH : LTAF → LTAI"
  const match = cellData.match(/(\w+)\s*:\s*(\w+)\s*[→->]\s*(\w+)/);

  if (match) {
    return {
      errorCode: match[1],       // TCCOH
      destinationICAO: match[2], // LTAF
      originICAO: match[3]       // LTAI
    };
  }

  return null;
}

/**
 * Group rows by cell_data and determine which rows should be highlighted
 * From index4.html:1628-1679
 */
export function processSequenceGroups(errorGroup: ErrorGroup) {
  // Group rows by cell_data
  const groups = new Map<string, Array<{ rowError: any; originalIndex: number }>>();

  errorGroup.rows.forEach((rowError, index) => {
    if (rowError.cell_data) {
      const sequence = parseErrorSequence(rowError.cell_data);
      if (sequence) {
        const key = rowError.cell_data; // Use full cell_data as key
        if (!groups.has(key)) {
          groups.set(key, []);
        }
        groups.get(key)!.push({ rowError, originalIndex: index });
      }
    }
  });

  // Determine which rows should be highlighted
  const highlightMap = new Map<number, boolean>();
  const sequenceErrors = new Map<string, SequenceError>();

  groups.forEach((groupRows, cellData) => {
    if (groupRows.length === 4) {
      // Highlight 2nd and 3rd rows (indices 1 and 2)
      highlightMap.set(groupRows[1].rowError.row_idx, true);
      highlightMap.set(groupRows[2].rowError.row_idx, true);
    }

    // Collect sequence for final summary
    if (groupRows.length > 0) {
      const sequence = parseErrorSequence(cellData);
      if (sequence) {
        const key = `${sequence.errorCode}_${sequence.destinationICAO}_${sequence.originICAO}`;
        sequenceErrors.set(key, sequence);
      }
    }
  });

  return { groups, highlightMap, sequenceErrors };
}

/**
 * Find mismatched cells in sequence for highlighting
 * From index4.html:1774-1789
 */
export function findMismatchedSequenceCells(rows: any[], columnOrder: string[]) {
  const highlightCells: Array<{ rowIdx: number; col: string }> = [];

  for (let i = 0; i < rows.length - 1; i++) {
    const currentRow = rows[i].rowData || rows[i].columns;
    const nextRow = rows[i + 1].rowData || rows[i + 1].columns;

    if (currentRow && nextRow) {
      if (currentRow['Destination ICAO'] !== nextRow['Origin ICAO']) {
        highlightCells.push({ rowIdx: i, col: 'Destination ICAO' });
        highlightCells.push({ rowIdx: i + 1, col: 'Origin ICAO' });
      }
    }
  }

  return highlightCells;
}

/**
 * Apply error box styling to cells containing "Error:" or "Details:"
 * From index4.html:1315-1333
 */
export function applyErrorBoxStyling(element: HTMLElement) {
  const tables = element.querySelectorAll('.data-table, .error-row-table, .sequence-table');

  tables.forEach(table => {
    const cells = table.querySelectorAll('td');
    cells.forEach(cell => {
      const text = cell.textContent || '';
      if (text.includes('Error:') || text.includes('Details:')) {
        cell.classList.add('error-info-cell');
        // Wrap content in span for styling
        if (!cell.querySelector('span')) {
          cell.innerHTML = `<span>${cell.innerHTML}</span>`;
        }
      }
    });
  });
}

/**
 * Mark last rows in sequence groups
 * From index4.html:1335-1350
 */
export function markLastInSequence(element: HTMLElement) {
  const tables = element.querySelectorAll('.data-table, .error-row-table, .sequence-table');

  tables.forEach(table => {
    const rows = table.querySelectorAll('tr');
    rows.forEach((row, index) => {
      if (row.classList.contains('sequence-error-row')) {
        const nextRow = rows[index + 1];
        if (!nextRow || !nextRow.classList.contains('sequence-error-row')) {
          row.classList.add('last-in-sequence');
        }
      }
    });
  });
}

/**
 * Create summary data for sequence errors
 */
export function createSequenceSummary(sequenceErrors: Map<string, SequenceError>) {
  const summaryItems: Array<{
    key: string;
    errorCode: string;
    destinationICAO: string;
    originICAO: string;
  }> = [];

  for (const [key, sequence] of sequenceErrors) {
    summaryItems.push({
      key,
      errorCode: sequence.errorCode,
      destinationICAO: sequence.destinationICAO,
      originICAO: sequence.originICAO
    });
  }

  return summaryItems;
}
