// Chat Service - Updated for app5.py API
// Base URL: https://tools.vurdhaan.com/api
// Requires Firebase authentication

import {
  ChatSession,
  ChatQueryResponse,
  LogEntry
} from '../types/chat';
import { getAuthToken } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://tools.vurdhaan.com/api';

/**
 * Get authorization headers with Firebase token
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken();
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
}

export const chatService = {
  /**
   * Initialize chat session for project
   * POST /api/projects/{project_id}/chat/initialize
   * From app5.py:292-328
   */
  async initializeSession(projectId: string): Promise<{ session_id: string; database_info: any }> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chat/initialize`, {
      method: 'POST',
      headers
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Chat initialization failed' }));
      throw new Error(error.error || 'Failed to initialize chat session');
    }

    return response.json();
  },

  /**
   * Send query to chat
   * POST /api/projects/{project_id}/chat/query
   * From app5.py:330-368
   */
  async sendQuery(projectId: string, query: string, sessionId?: string): Promise<ChatQueryResponse> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chat/query`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Query failed' }));
      throw new Error(error.error || 'Failed to process query');
    }

    return response.json();
  },

  /**
   * Get project details (includes session info if available)
   * GET /api/projects/{project_id}
   * From app5.py:184-204
   */
  async getProjectSession(projectId: string): Promise<any> {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch project');
    }

    return response.json();
  },

  /**
   * Send debug log to server (optional - app5.py doesn't have this endpoint)
   */
  async logDebug(message: string, data?: any, sessionId?: string): Promise<void> {
    // Log to console only as app5.py doesn't have logging endpoint
    console.log('[DEBUG]', message, data);
  },

  /**
   * Send error log to server (optional - app5.py doesn't have this endpoint)
   */
  async logError(message: string, data?: any, sessionId?: string): Promise<void> {
    // Log to console only as app5.py doesn't have logging endpoint
    console.error('[ERROR]', message, data);
  },

  /**
   * Generate a unique session ID
   */
  generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }
};
