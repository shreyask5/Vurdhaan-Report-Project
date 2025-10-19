/**
 * Project Chat Service
 * Handles chat initialization and operations for project-based chat sessions
 * Integrates with app5.py backend API
 */

import { chatApi } from './api';

export interface ProjectChatSession {
  sessionId: string;
  projectId: string;
  databaseInfo?: {
    clean_flights?: {
      row_count: number;
      columns: string[];
    };
    error_flights?: {
      row_count: number;
      columns: string[];
    };
  };
  created_at?: string;
  expires_at?: string;
}

export interface ChatQueryResponse {
  status: 'success' | 'error';
  response: string;
  sql_query?: string;
  table_data?: any[];
  total_rows?: number;
  error?: string;
}

class ProjectChatService {
  /**
   * Initialize chat session for a project
   * Uses project's existing clean_data.csv and errors_data.csv files
   */
  async initializeFromProject(projectId: string): Promise<ProjectChatSession> {
    console.log('[PROJECT CHAT] Initializing chat for project:', projectId);

    try {
      const response = await chatApi.initialize(projectId);

      console.log('[PROJECT CHAT] Initialization response:', response);

      return {
        sessionId: response.session_id,
        projectId: projectId,
      };
    } catch (error) {
      console.error('[PROJECT CHAT] Failed to initialize chat:', error);
      throw new Error(`Failed to initialize chat session: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Send a query to the chat session
   */
  async sendQuery(
    projectId: string,
    query: string,
    sessionId?: string
  ): Promise<ChatQueryResponse> {
    console.log('[PROJECT CHAT] Sending query:', query);

    try {
      const response = await chatApi.query(projectId, query, sessionId);

      console.log('[PROJECT CHAT] Query response:', response);

      return response as ChatQueryResponse;
    } catch (error) {
      console.error('[PROJECT CHAT] Query failed:', error);
      throw new Error(`Query failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Log debug information (for troubleshooting)
   */
  logDebug(message: string, data?: any) {
    console.log(`[PROJECT CHAT DEBUG] ${message}`, data || '');
  }

  /**
   * Log error information
   */
  logError(message: string, error?: any) {
    console.error(`[PROJECT CHAT ERROR] ${message}`, error || '');
  }
}

export const projectChatService = new ProjectChatService();
