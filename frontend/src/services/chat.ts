// Chat Service
// Handles all chat-related API calls
// Based on chat.js

import {
  ChatSession,
  ChatQueryResponse,
  ChatInitializeRequest,
  ChatInitializeResponse,
  UploadFilesResponse,
  LogEntry
} from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const chatService = {
  /**
   * Upload files for chat session
   * POST /upload_files
   * From chat.js:133-143
   */
  async uploadFiles(cleanFile: File, errorFile: File): Promise<UploadFilesResponse> {
    const formData = new FormData();
    formData.append('clean_data', cleanFile);
    formData.append('error_data', errorFile);

    const response = await fetch(`${API_BASE_URL}/upload_files`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error('Failed to upload files');
    }

    return response.json();
  },

  /**
   * Initialize chat session
   * POST /chat/initialize
   * From chat.js:145-173
   */
  async initializeSession(
    sessionId: string,
    cleanFlightsPath: string,
    errorFlightsPath: string
  ): Promise<ChatInitializeResponse> {
    const response = await fetch(`${API_BASE_URL}/chat/initialize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        clean_flights_path: cleanFlightsPath,
        error_flights_path: errorFlightsPath
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Initialization failed' }));
      throw new Error(error.message || 'Failed to initialize chat session');
    }

    return response.json();
  },

  /**
   * Get session status
   * GET /chat/{session_id}/status
   * From chat.js:56-67
   */
  async getSessionStatus(sessionId: string): Promise<ChatSession> {
    const response = await fetch(`${API_BASE_URL}/chat/${sessionId}/status`);

    if (!response.ok) {
      throw new Error(`Session not found or expired (Status: ${response.status})`);
    }

    return response.json();
  },

  /**
   * Send query to chat
   * POST /chat/{session_id}/query
   * From chat.js:197-227
   */
  async sendQuery(sessionId: string, query: string): Promise<ChatQueryResponse> {
    const response = await fetch(`${API_BASE_URL}/chat/${sessionId}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query })
    });

    if (!response.ok) {
      throw new Error('Failed to process query');
    }

    return response.json();
  },

  /**
   * Send debug log to server
   * POST /api/log
   * From chat.js:641-650
   */
  async logDebug(message: string, data?: any, sessionId?: string): Promise<void> {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: 'debug',
      message,
      data,
      session_id: sessionId
    };

    try {
      await fetch(`${API_BASE_URL}/api/log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(logEntry)
      });
    } catch (error) {
      // Silently fail - don't want logging to break the app
      console.warn('Failed to send log to server:', error);
    }
  },

  /**
   * Send error log to server
   * POST /api/log
   * From chat.js:641-650
   */
  async logError(message: string, data?: any, sessionId?: string): Promise<void> {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: 'error',
      message,
      data,
      session_id: sessionId
    };

    try {
      await fetch(`${API_BASE_URL}/api/log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(logEntry)
      });
    } catch (error) {
      // Silently fail - don't want logging to break the app
      console.warn('Failed to send log to server:', error);
    }
  },

  /**
   * Generate a unique session ID
   * From chat.js:130-131
   */
  generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }
};
