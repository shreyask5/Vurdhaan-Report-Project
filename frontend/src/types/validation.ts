/**
 * TypeScript types for CSV validation and error handling
 */

export type FuelMethod = 'Block Off - Block On' | 'Method B';
export type DateFormat = 'DMY' | 'MDY';
export type ErrorCategory = 'SEQUENCE_ERRORS' | 'DATE_ERRORS' | 'FUEL_ERRORS' | 'ICAO_ERRORS' | 'OTHER';

export interface ColumnMapping {
  [requiredColumn: string]: string; // Maps required column name to CSV column name
}

export interface ValidationParams {
  monitoring_year: string;
  date_format: DateFormat;
  flight_starts_with: string;
  fuel_method: FuelMethod;
  column_mapping: ColumnMapping;
}

export interface ErrorRow {
  row_idx: number;
  cell_data?: string;
  file_level?: boolean;
  columns?: string[];
}

export interface ErrorGroup {
  reason: string;
  rows: ErrorRow[];
  count: number;
}

export interface ErrorCategory {
  name: string;
  errors: ErrorGroup[];
  total_count: number;
}

export interface ValidationErrorData {
  categories: ErrorCategory[];
  total_errors: number;
  total_clean_rows: number;
  rows_data: { [key: number]: any };
}

export interface ValidationResult {
  is_valid: boolean;
  error_data?: ValidationErrorData;
  file_id?: string;
  filename?: string;
  clean_csv_path?: string;
  errors_csv_path?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  sql_query?: string;
  table_data?: any[];
  timestamp?: string;
}

export interface ChatSession {
  session_id: string;
  project_id: string;
  expires_at: string;
  database_info?: {
    clean_flights?: {
      table_name: string;
      row_count: number;
      columns: string[];
    };
    error_flights?: {
      table_name: string;
      row_count: number;
      columns: string[];
    };
  };
}

export interface ChatQueryResponse {
  status: string;
  response: string;
  answer?: string;
  sql_query?: string;
  table_data?: any[];
  metadata?: {
    method?: 'summary' | 'sql';
  };
}
