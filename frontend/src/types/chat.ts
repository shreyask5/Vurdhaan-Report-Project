// TypeScript interfaces for AI chat
// Based on chat.js and chat.html

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sql_query?: string;
  table_data?: any[];
  timestamp: Date;
  metadata?: {
    tokens_used?: number;
    model?: string;
    cache_savings_pct?: number;
    function_calls?: number;
  };
}

export interface ChatMetadata {
  id: string;
  name: string;
  project_id?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string;
  is_active?: boolean;
}

export interface StoredChatMessage extends ChatMessage {
  chat_id: string;
}

export interface ChatSession {
  session_id: string;
  expires_at: string;
  database_info?: {
    clean_flights_count?: number;
    error_flights_count?: number;
    total_flights?: number;
  };
}

export interface ChatQueryRequest {
  query: string;
}

export interface ChatQueryResponse {
  answer?: string;
  response?: string;
  sql_query?: string;
  table_data?: any[];
  metadata?: {
    method?: 'summary' | 'sql';
  };
}

export interface ChatInitializeRequest {
  session_id: string;
  clean_flights_path: string;
  error_flights_path: string;
}

export interface ChatInitializeResponse {
  success: boolean;
  session_id: string;
  message?: string;
}

export interface UploadFilesResponse {
  success: boolean;
  clean_flights_path: string;
  error_flights_path: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'error';
  message: string;
  data?: any;
  session_id?: string;
}

// Suggested questions from chat.html:748-764
export const SUGGESTED_QUESTIONS = [
  'Summarize flight operations for the last quarter',
  'Show aircraft with fuel efficiency issues',
  'Compare error rates between different aircraft types',
  'Identify flights with the highest fuel consumption'
];
