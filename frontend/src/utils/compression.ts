// LZ-String compression utilities
// Based on index4.html:2226-2310, 2312-2494

import { ErrorData, OptimizedErrorData } from '../types/validation';

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
function restoreOriginalErrorStructure(optimizedData: OptimizedErrorData): ErrorData {
  try {
    console.log('🔄 Restoring original error structure from optimized format...');

    const { meta, categories: categoriesData } = optimizedData;
    const { field_map, schemas } = meta;

    // Create reverse map for field indices
    const reverseFieldMap: Record<number, string> = {};
    Object.entries(field_map).forEach(([field, index]) => {
      reverseFieldMap[index as number] = field;
    });

    console.log('Field map:', field_map);
    console.log('Schemas:', schemas);

    // Restore categories
    const categories = categoriesData.map((catData: any[]) => {
      const category: any = {};

      // Restore category fields based on schema
      schemas.category.forEach((field, idx) => {
        category[field] = catData[idx];
      });

      // Restore error groups
      if (category.errors && Array.isArray(category.errors)) {
        category.errors = category.errors.map((errData: any[]) => {
          const errorGroup: any = {};

          // Restore error group fields
          schemas.error_group.forEach((field, idx) => {
            errorGroup[field] = errData[idx];
          });

          // Restore rows
          if (errorGroup.rows && Array.isArray(errorGroup.rows)) {
            errorGroup.rows = errorGroup.rows.map((rowData: any[]) => {
              const row: any = {};

              // Restore row fields
              schemas.row_error.forEach((field, idx) => {
                row[field] = rowData[idx];
              });

              // Restore columns object from array
              if (row.columns && Array.isArray(row.columns)) {
                const columnsArray = row.columns;
                row.columns = {};

                columnsArray.forEach((value: any, idx: number) => {
                  const fieldName = reverseFieldMap[idx];
                  if (fieldName) {
                    row.columns[fieldName] = value;
                  }
                });
              }

              return row;
            });
          }

          return errorGroup;
        });
      }

      return category;
    });

    const restoredData: ErrorData = { categories };

    console.log('✅ Successfully restored error structure');
    console.log('Categories count:', categories.length);

    return restoredData;

  } catch (error) {
    console.error('❌ [ERROR] Structure restoration failed:', error);
    throw new Error(`Failed to restore error structure: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Checks if response is compressed
 */
export function isCompressedResponse(data: any): boolean {
  return data && typeof data === 'object' && data.compressed === true && typeof data.compressed_data === 'string';
}
