// LZ-String compression utilities
// Based on index4.html:2226-2310, 2312-2494

import { ErrorData, OptimizedErrorData, PaginatedErrorData } from '../types/validation';

/**
 * Decompresses LZ-String compressed error report
 * From index4.html:2226-2251
 */
export async function decompressLZStringErrorReport(compressedData: string): Promise<ErrorData> {
  try {
    console.log('Starting LZ-String decompression...');

    // Check if LZString is available (loaded from CDN)
    if (typeof (window as any).LZString === 'undefined') {
      throw new Error('LZ-String library not loaded. Please check your internet connection and try again.');
    }

    const LZString = (window as any).LZString;

    // Step 1: LZ-String decompression
    const jsonStr = LZString.decompressFromBase64(compressedData);

    if (!jsonStr) {
      throw new Error('Failed to decompress data. The data may be corrupted.');
    }

    // Parse the decompressed JSON
    const optimizedData: OptimizedErrorData = JSON.parse(jsonStr);

    console.log(`LZ-String decompression successful: ${compressedData.length.toLocaleString()} → ${jsonStr.length.toLocaleString()} characters`);
    console.log(`Compression ratio: ${((1 - compressedData.length / jsonStr.length) * 100).toFixed(1)}%`);

    // Step 2: Restore original structure
    return restoreOriginalErrorStructure(optimizedData);

  } catch (error) {
    console.error('❌ [ERROR] Decompression failed:', error);
    throw new Error(`Failed to decompress error data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Restores original error structure from optimized format
 * From index4.html:2312-2494
 */
function restoreOriginalErrorStructure(optimizedData: any): ErrorData {
  try {
    console.log('🔄 Restoring original error structure...');

    // Validate input structure
    if (!optimizedData || !optimizedData.meta) {
      throw new Error('Invalid optimized data structure: missing meta section');
    }

    // Get field mapping for restoration
    const fieldMap = optimizedData.meta.fm; // field map
    if (!fieldMap) {
      throw new Error('Invalid optimized data structure: missing field map');
    }

    // Step 1: Restore row data with full field names
    const restoredRows: Record<number, any> = {};
    const rowsData = optimizedData.rd || {};

    for (const [rowIdx, rowData] of Object.entries(rowsData)) {
      const restoredRow: any = {};

      for (const [shortKey, value] of Object.entries(rowData as any)) {
        if (shortKey === 'err') {
          // Handle error field
          restoredRow['error'] = value;
        } else {
          // Restore full field name
          const fullKey = fieldMap[shortKey] || shortKey;
          restoredRow[fullKey] = value;
        }
      }

      restoredRows[parseInt(rowIdx)] = restoredRow;
    }

    // Step 2: Restore category structure
    const categories = optimizedData.c || [];
    const restoredCategories = categories.map((category: any) => ({
      name: category.n || '', // name
      errors: (category.e || []).map((error: any) => ({ // errors
        reason: error.r || '', // reason
        rows: (error.rows || []).map((row: any) => {
          if (row.fl) { // file_level
            return {
              file_level: true,
              cell_data: row.cd || '',
              columns: row.cols || []
            };
          } else {
            return {
              row_idx: row.idx,
              cell_data: row.cd || '',
              columns: row.cols || []
            };
          }
        })
      }))
    }));

    // Step 3: Restore summary structure
    const summary = optimizedData.meta.s || {};
    const restoredSummary = {
      total_errors: summary.te || 0,
      error_rows: summary.er || 0,
      categories: summary.c || {}
    };

    // Step 4: Construct final restored structure
    const restoredData: ErrorData = {
      summary: restoredSummary,
      rows_data: restoredRows,
      categories: restoredCategories
    };

    console.log('✅ Structure restoration completed');
    console.log('Restored data summary:', restoredData.summary);
    console.log('[DECOMPRESSION] restoredData.rows_data type:', typeof restoredData.rows_data);
    console.log('[DECOMPRESSION] restoredData.rows_data keys:', Object.keys(restoredData.rows_data));
    console.log('[DECOMPRESSION] restoredData.rows_data is array?', Array.isArray(restoredData.rows_data));

    // TEMPORARY: Print entire decompressed JSON structure
    console.log('═══════════════════════════════════════════════════════════');
    console.log('FULL DECOMPRESSED ERROR DATA:');
    console.log('═══════════════════════════════════════════════════════════');
    console.log(JSON.stringify(restoredData, null, 2));
    console.log('═══════════════════════════════════════════════════════════');
    console.log('ROWS_DATA SAMPLE (first 3 rows):');
    const rowKeys = Object.keys(restoredData.rows_data).slice(0, 3);
    rowKeys.forEach(key => {
      console.log(`Row ${key}:`, restoredData.rows_data[parseInt(key)]);
    });
    console.log('═══════════════════════════════════════════════════════════');

    // Validate restored structure
    if (!restoredData.summary || typeof restoredData.summary.total_errors !== 'number') {
      throw new Error('Restored data validation failed: invalid summary structure');
    }

    return restoredData;

  } catch (error) {
    console.error('❌ [ERROR] Failed to restore error structure:', error);
    throw new Error(`Structure restoration failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Decompresses LZ-String compressed paginated error page
 * Paginated format is NOT optimized (uses full structure), so just decompress and parse
 */
export async function decompressLZStringPaginatedPage(compressedData: string): Promise<PaginatedErrorData> {
  try {
    console.log('[COMPRESSION] Starting LZ-String decompression for paginated page...');
    console.log('[COMPRESSION] Compressed data length:', compressedData.length);

    // Check if LZString is available (loaded from CDN)
    if (typeof (window as any).LZString === 'undefined') {
      throw new Error('LZ-String library not loaded. Please check your internet connection and try again.');
    }

    const LZString = (window as any).LZString;

    // LZ-String decompression
    const jsonStr = LZString.decompressFromBase64(compressedData);

    if (!jsonStr) {
      throw new Error('Failed to decompress paginated data. The data may be corrupted.');
    }

    console.log('[COMPRESSION] Decompressed JSON length:', jsonStr.length);
    console.log('[COMPRESSION] Compression ratio:', ((1 - compressedData.length / jsonStr.length) * 100).toFixed(1) + '%');

    // Parse the decompressed JSON (already in correct PaginatedErrorData format)
    const paginatedData: PaginatedErrorData = JSON.parse(jsonStr);

    console.log('[COMPRESSION] Paginated page decompression successful:', {
      category: paginatedData.category_name,
      page: paginatedData.page,
      totalPages: paginatedData.total_pages,
      errorsOnPage: paginatedData.errors_on_page,
      rowsDataKeys: paginatedData.rows_data ? Object.keys(paginatedData.rows_data).length : 0,
      errorGroups: paginatedData.error_groups?.length || 0
    });

    // Validate structure
    if (!paginatedData.category_name || typeof paginatedData.page !== 'number') {
      throw new Error('Invalid paginated data structure: missing required fields');
    }

    return paginatedData;

  } catch (error) {
    console.error('❌ [ERROR] Paginated page decompression failed:', error);
    throw new Error(`Failed to decompress paginated error data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Checks if response is compressed
 */
export function isCompressedResponse(data: any): boolean {
  return data && typeof data === 'object' && data.compressed === true && typeof data.compressed_data === 'string';
}
