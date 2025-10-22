// TypeScript interfaces for CSV validation
// Based on index4.html data structures

export type FuelMethod = "Block Off - Block On" | "Method B";

export type DateFormat = "DMY" | "MDY";

export type SchemeType = "CORSIA" | "EU ETS" | "UK ETS" | "CH ETS" | "ReFuelEU";

export type AirlineSize = "small" | "medium" | "large";

export interface SchemeSelection {
  scheme: SchemeType;
  airline_size: AirlineSize;
}

export interface MonitoringPlanData {
  monitoring_plan_processes: {
    CORSIA?: string;
    EU_ETS?: string;
    UK_ETS?: string;
    CH_ETS?: string;
    ReFuelEU?: string;
  };
  basic_info: {
    airline_name?: string;
    registration_details?: string;
    contact_info?: string;
    version?: string;
    date?: string;
  };
  method: {
    fuel_monitoring_methodology?: string;
    calculation_methods?: string;
    standards_references?: string;
  };
  fuel_data_collection: {
    collection_method?: "automatic" | "manual" | "hybrid";
    details?: string;
  };
  primary_data_source: {
    is_automatic?: boolean;
    system_used?: string;
    frequency?: string;
    accuracy?: string;
  };
  secondary_source: {
    uses_paper_logs?: boolean;
    backup_procedures?: string;
    validation_methods?: string;
  };
  geographical_presence: {
    is_eu_based?: boolean;
    is_non_eu_based?: boolean;
    primary_region?: string;
    scheme_priority?: {
      CORSIA?: "high" | "standard" | "low";
      EU_ETS?: "high" | "standard" | "low";
      UK_ETS?: "high" | "standard" | "low";
      CH_ETS?: "high" | "standard" | "low";
      ReFuelEU?: "high" | "standard" | "low";
    };
  };
  extraction_metadata?: {
    model?: string;
    reasoning_effort?: string;
    extracted_at?: string;
  };
}

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
  highlight?: boolean; // For sequence error highlighting
}

export interface ErrorGroup {
  reason: string;
  rows: ErrorRow[];
  columns?: string[];
}

export interface ErrorCategory {
  name: string;
  errors: ErrorGroup[];
  file_level?: boolean;
}

// Summary structure from backend
export interface ErrorSummary {
  total_errors: number;
  error_rows: number;
  categories: Record<string, number>;
}

export interface ErrorData {
  summary: ErrorSummary;
  rows_data: Record<number, any>;
  categories: ErrorCategory[];
}

// ========================================================================
// PAGINATED ERROR REPORTING STRUCTURES
// ========================================================================

// Paginated error metadata - returned by /api/projects/{id}/errors/metadata
export interface ErrorMetadata {
  total_errors: number;
  error_rows: number;
  error_categories: number;
  categories: CategoryMetadata[];
}

export interface CategoryMetadata {
  name: string;
  total_errors: number;
  total_pages: number;
}

// Paginated error data (per category, per page) - returned by /api/projects/{id}/errors?category=X&page=N
export interface PaginatedErrorData {
  category_name: string;
  page: number;
  total_pages: number;
  errors_on_page: number;
  summary: {
    total_errors: number;
    error_rows: number;
  };
  rows_data: Record<number, any>;
  error_groups: ErrorGroup[];
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
