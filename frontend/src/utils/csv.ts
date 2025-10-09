// CSV utility functions
// Based on index4.html:1364-1429

/**
 * Escapes a CSV field value according to RFC 4180
 * From index4.html:1364-1377
 */
export function escapeCSVField(field: any): string {
  if (field === null || field === undefined) return '';

  let fieldStr = String(field);

  // If field contains comma, newline, carriage return, or quote, wrap in quotes and escape internal quotes
  if (fieldStr.includes(',') || fieldStr.includes('\n') || fieldStr.includes('\r') || fieldStr.includes('"')) {
    fieldStr = '"' + fieldStr.replace(/"/g, '""') + '"';
  }

  return fieldStr;
}

/**
 * Downloads data as a CSV file
 * From index4.html:1379-1429
 */
export function downloadCSV(data: any[], filename: string): void {
  try {
    console.log('📥 [DEBUG] Starting CSV download:', filename, 'Rows:', data.length);

    if (!data || data.length === 0) {
      alert('No data available to download');
      return;
    }

    // Get column headers from first row
    const columns = Object.keys(data[0]);

    // Create CSV content
    let csvContent = '';

    // Add header row
    csvContent += columns.map(col => escapeCSVField(col)).join(',') + '\n';

    // Add data rows
    data.forEach(row => {
      const rowData = columns.map(col => {
        const value = row[col];
        return escapeCSVField(value);
      });
      csvContent += rowData.join(',') + '\n';
    });

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up the URL object
    URL.revokeObjectURL(url);

    console.log('✅ [DEBUG] CSV download completed successfully');

  } catch (error) {
    console.error('❌ [ERROR] CSV download failed:', error);
    alert('Failed to download CSV file. Please try again.');
  }
}

/**
 * Reads CSV columns from a file
 * From index4.html:1761-1780
 */
export function readCSVColumns(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = function(e) {
      try {
        const text = e.target?.result as string;
        const firstLine = text.split('\n')[0].trim();

        // Remove quotes and trim whitespace to match backend processing
        const columns = firstLine.split(',').map(col =>
          col.replace(/^["']|["']$/g, '').trim()
        );

        console.log('Detected CSV columns:', columns);
        console.log('Column count:', columns.length);

        resolve(columns);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = reject;
    reader.readAsText(file);
  });
}

/**
 * Formats file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Validates if file is a CSV
 */
export function isCSVFile(file: File): boolean {
  return file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv');
}

/**
 * Download category CSV with enriched data
 * From index4.html:1431-1467
 */
export function downloadCategoryCSV(
  categoryName: string,
  errorGroups: any[],
  rowsData: Record<number, any>
): void {
  try {
    const sanitizedName = categoryName.replace(/[^a-zA-Z0-9]/g, '_');
    const filename = `${sanitizedName}_errors.csv`;

    console.log('📂 [DEBUG] Downloading category CSV:', categoryName);

    const allRowsData: any[] = [];

    // Process each error group in the category
    errorGroups.forEach(errorGroup => {
      errorGroup.rows.forEach((rowError: any) => {
        if (!rowError.file_level) {
          const rowData = rowsData[rowError.row_idx] || {};
          const enrichedRow = {
            'Error_Category': categoryName,
            'Error_Reason': errorGroup.reason,
            'Error_Details': rowError.cell_data || '',
            'Row_Index': rowError.row_idx,
            ...rowData
          };
          allRowsData.push(enrichedRow);
        }
      });
    });

    downloadCSV(allRowsData, filename);

  } catch (error) {
    console.error('💥 [DEBUG] Category CSV download failed:', error);
    alert('Failed to download category CSV: ' + (error as Error).message);
  }
}

/**
 * Download reason group CSV with enriched data
 * From index4.html:1469-1503
 */
export function downloadReasonGroupCSV(
  categoryName: string,
  errorGroup: any,
  rowsData: Record<number, any>
): void {
  try {
    const sanitizedReason = errorGroup.reason.replace(/[^a-zA-Z0-9]/g, '_');
    const filename = `${sanitizedReason}_errors.csv`;

    console.log('📊 [DEBUG] Downloading reason group CSV:', errorGroup.reason);

    const reasonRowsData: any[] = [];

    errorGroup.rows.forEach((rowError: any) => {
      if (!rowError.file_level) {
        const rowData = rowsData[rowError.row_idx] || {};
        const enrichedRow = {
          'Error_Category': categoryName,
          'Error_Reason': errorGroup.reason,
          'Error_Details': rowError.cell_data || '',
          'Row_Index': rowError.row_idx,
          ...rowData
        };
        reasonRowsData.push(enrichedRow);
      }
    });

    downloadCSV(reasonRowsData, filename);

  } catch (error) {
    console.error('💥 [DEBUG] Reason group CSV download failed:', error);
    alert('Failed to download reason group CSV: ' + (error as Error).message);
  }
}

/**
 * Download sequence table CSV
 * From index4.html:1505-1554
 */
export function downloadSequenceTableCSV(
  tableElement: HTMLTableElement,
  headerText: string
): void {
  try {
    const filename = `${headerText.replace(/[^a-zA-Z0-9]/g, '_')}.csv`;

    console.log('🔄 [DEBUG] Downloading sequence table CSV:', filename);

    const tableData: any[] = [];
    const headers: string[] = [];

    // Get headers
    const headerRow = tableElement.querySelector('thead tr');
    if (headerRow) {
      headerRow.querySelectorAll('th').forEach(th => {
        headers.push(th.textContent?.trim() || '');
      });
    }

    // Get data rows
    const dataRows = tableElement.querySelectorAll('tbody tr');
    dataRows.forEach(row => {
      const rowData: any = {};
      row.querySelectorAll('td').forEach((td, index) => {
        const input = td.querySelector('input') as HTMLInputElement;
        const cellValue = input ? input.value : td.textContent?.trim() || '';
        rowData[headers[index] || `Column_${index + 1}`] = cellValue;
      });
      tableData.push(rowData);
    });

    downloadCSV(tableData, filename);

  } catch (error) {
    console.error('💥 [DEBUG] Sequence table CSV download failed:', error);
    alert('Failed to download sequence table CSV: ' + (error as Error).message);
  }
}
