// Validation utility functions
// Based on index4.html:1608-1627, 1630-1668

import { SequenceError, ErrorGroup, ErrorRow } from '../types/validation';

/**
 * Parses error sequence from cell_data
 * From index4.html:1608-1627
 *
 * Pattern: "TCCOH : LTAF → LTAI"
 * Returns: { errorCode: "TCCOH", destinationICAO: "LTAF", originICAO: "LTAI" }
 */
export function parseErrorSequence(cellData?: string): SequenceError | null {
  if (!cellData) return null;

  // Ensure cellData is a string
  if (typeof cellData !== 'string') {
    return null;
  }

  // Match pattern like "TCCOH : LTAF → LTAI"
  const match = cellData.match(/(\w+)\s*:\s*(\w+)\s*→\s*(\w+)/);
  if (match) {
    console.log('Parsed sequence:', match);
    return {
      errorCode: match[1],      // TCCOH
      destinationICAO: match[2], // LTAF
      originICAO: match[3]       // LTAI
    };
  }
  return null;
}

/**
 * Groups sequence errors and determines which rows should be highlighted
 * From index4.html:1630-1668
 */
export function processSequenceGroups(errorGroup: ErrorGroup): {
  groups: Map<string, Array<{ rowError: ErrorRow; originalIndex: number }>>;
  highlightMap: Map<number, boolean>;
} {
  const groups = new Map<string, Array<{ rowError: ErrorRow; originalIndex: number }>>();

  // Group errors by sequence key
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

  // Create highlight map for 2nd and 3rd rows in 4-row sequences
  const highlightMap = new Map<number, boolean>();

  groups.forEach((groupRows, cellData) => {
    // Sort by row_idx
    groupRows.sort((a, b) => a.rowError.row_idx - b.rowError.row_idx);

    // If group has exactly 4 rows, highlight the 2nd and 3rd
    if (groupRows.length === 4) {
      highlightMap.set(groupRows[1].rowError.row_idx, true);
      highlightMap.set(groupRows[2].rowError.row_idx, true);
    }
  });

  return { groups, highlightMap };
}

/**
 * Determines if a cell should be highlighted in sequence error comparison
 * Red-highlight only Destination/Origin ICAO cells that don't match
 */
export function shouldHighlightSequenceCell(
  rowIndex: number,
  columnName: string,
  currentValue: string,
  nextOriginICAO?: string,
  currentDestinationICAO?: string
): boolean {
  // Only highlight Destination ICAO and Origin ICAO columns
  if (columnName !== 'Destination ICAO' && columnName !== 'Origin ICAO') {
    return false;
  }

  // For Destination ICAO, check if it matches next row's Origin ICAO
  if (columnName === 'Destination ICAO' && nextOriginICAO !== undefined) {
    return currentValue !== nextOriginICAO;
  }

  return false;
}

/**
 * Applies error box styling to table cells
 * From index4.html:1315-1331
 */
export function applyErrorBoxStyling(container: HTMLElement): void {
  const tables = container.querySelectorAll('.data-table, .error-row-table, .sequence-table');

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
 * Marks last rows in sequence groups
 * From index4.html:1334-1347
 */
export function markLastInSequence(container: HTMLElement): void {
  const tables = container.querySelectorAll('.data-table, .error-row-table, .sequence-table');

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
