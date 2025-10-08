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
