/**
 * Chat Service - Handles AI chat sessions and queries
 */

import { auth } from './firebase';
import type { ChatSession, ChatQueryResponse, ChatMessage } from '@/types/validation';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5002/api';

async function getAuthToken(): Promise<string> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('Not authenticated');
  }
  return await user.getIdToken();
}

export const chatService = {
  /**
   * Initialize a new chat session for a project
   */
  async initializeSession(projectId: string): Promise<ChatSession> {
    const token = await getAuthToken();

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chat/initialize`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to initialize chat' }));
      throw new Error(error.error || 'Failed to initialize chat session');
    }

    return response.json();
  },

  /**
   * Send a query to the chat session
   */
  async sendQuery(
    projectId: string,
    query: string,
    sessionId?: string
  ): Promise<ChatQueryResponse> {
    const token = await getAuthToken();

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/chat/query`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Query failed' }));
      throw new Error(error.error || 'Failed to send query');
    }

    return response.json();
  },

  /**
   * Get chat history for a session (if implemented in backend)
   */
  async getChatHistory(
    projectId: string,
    sessionId: string
  ): Promise<{ messages: ChatMessage[] }> {
    const token = await getAuthToken();

    const response = await fetch(
      `${API_BASE_URL}/projects/${projectId}/chat/history?session_id=${sessionId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to fetch history' }));
      throw new Error(error.error || 'Failed to fetch chat history');
    }

    return response.json();
  },

  /**
   * Export table data to CSV
   */
  exportTableToCSV(data: any[], filename: string = 'query_results.csv'): void {
    if (!data || data.length === 0) {
      throw new Error('No data to export');
    }

    // Get headers from first row
    const headers = Object.keys(data[0]);

    // Create CSV content
    const csvContent = [
      headers.join(','), // Header row
      ...data.map(row =>
        headers.map(header => {
          const value = row[header];
          // Handle values that contain commas or quotes
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? '';
        }).join(',')
      ),
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Get suggested questions for a dataset
   */
  getSuggestedQuestions(): string[] {
    return [
      'How many total flights are in the dataset?',
      'What is the total fuel consumption?',
      'Which route has the highest fuel consumption?',
      'Show me flights from JFK airport',
      'What is the average fuel uplift per flight?',
      'List all unique departure airports',
      'Show flights longer than 5 hours',
      'What is the fuel consumption by month?',
    ];
  },

  /**
   * Format SQL query for display
   */
  formatSQL(sql: string): string {
    // Basic SQL formatting for readability
    return sql
      .replace(/\bSELECT\b/gi, 'SELECT')
      .replace(/\bFROM\b/gi, '\nFROM')
      .replace(/\bWHERE\b/gi, '\nWHERE')
      .replace(/\bGROUP BY\b/gi, '\nGROUP BY')
      .replace(/\bORDER BY\b/gi, '\nORDER BY')
      .replace(/\bLIMIT\b/gi, '\nLIMIT')
      .replace(/\bJOIN\b/gi, '\nJOIN')
      .replace(/\bAND\b/gi, '\n  AND')
      .replace(/\bOR\b/gi, '\n  OR')
      .trim();
  },
};

export default chatService;
