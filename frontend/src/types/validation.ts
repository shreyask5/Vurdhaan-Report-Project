// TypeScript interfaces for CSV validation
// Based on index4.html data structures

export type FuelMethod = "Block Off - Block On" | "Method B";

export type DateFormat = "DMY" | "MDY";

export interface ValidationParams {
  monitoring_year: string;
  date_format: DateFormat;
  flight_starts_with: string;
}

export interface ColumnMapping {
  [requiredColumn: string]: string; // Maps required column to CSV column
}

export interface ValidationFormData extends ValidationParams {
  column_mapping: ColumnMapping;
  fuel_method: FuelMethod;
}

// Error structures from index4.html:2603-2680
export interface ErrorRow {
  row_idx: number;
  cell_data?: string;
  columns: Record<string, any>;
  file_level?: boolean;
}

export interface ErrorGroup {
  reason: string;
  rows: ErrorRow[];
  columns: string[];
}

export interface ErrorCategory {
  name: string;
  errors: ErrorGroup[];
  file_level?: boolean;
}

export interface ErrorData {
  categories: ErrorCategory[];
  total_errors?: number;
  affected_rows?: number;
}

// Sequence error structure from index4.html:1608-1627
export interface SequenceError {
  errorCode: string;
  destinationICAO: string;
  originICAO: string;
}

// Correction structure from index4.html:2841-2871
export interface Correction {
  row_idx: number;
  column: string;
  old_value: any;
  new_value: any;
}

// Upload response
export interface UploadResponse {
  file_id: string;
  success: boolean;
  message?: string;
  errors?: ErrorData;
}

// Compressed response from index4.html:2226-2251
export interface CompressedErrorResponse {
  compressed: boolean;
  compressed_data: string;
}

// Optimized error structure for decompression (index4.html:2312-2494)
export interface OptimizedErrorData {
  meta: {
    field_map: Record<string, number>;
    schemas: {
      category: string[];
      error_group: string[];
      row_error: string[];
    };
  };
  categories: any[][];
}

// Fuel method column definitions from index4.html:1571-1605
export const FUEL_METHOD_COLUMNS: Record<FuelMethod, string[]> = {
  "Block Off - Block On": [
    "Date",
    "A/C Registration",
    "Flight No",
    "A/C Type",
    "ATD (UTC) Block Off",
    "ATA (UTC) Block On",
    "Origin ICAO",
    "Destination ICAO",
    "Block Off Fuel",
    "Block On Fuel",
    "Fuel Consumption"
  ],
  "Method B": [
    "Date",
    "A/C Registration",
    "Flight No",
    "A/C Type",
    "ATD (UTC) Block Off",
    "ATA (UTC) Block On",
    "Origin ICAO",
    "Destination ICAO",
    "Uplift weight",
    "Remaining Fuel From Prev. Flight",
    "Block On Fuel",
    "Fuel Consumption"
  ]
};
