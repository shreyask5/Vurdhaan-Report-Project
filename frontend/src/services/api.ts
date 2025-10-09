/**
 * API Service Client for Vurdhaan Report Project
 * Handles all API communication with the Flask backend (app5.py)
 */

import { auth } from './firebase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5002/api';

// Types
export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'processing' | 'completed' | 'error';
  ai_chat_enabled: boolean;
  save_files_on_server: boolean;
  created_at: string;
  updated_at?: string;
  has_file?: boolean;
  validation_status?: boolean;
  error_count?: number;
  upload_completed?: boolean;
  error_summary?: {
    total_errors: number;
    total_clean_rows: number;
    has_errors: boolean;
    categories_count: number;
    top_error: string;
  };
  file_metadata?: {
    filename: string;
    start_date: string;
    end_date: string;
    date_format: string;
    flight_starts_with: string;
    fuel_method: string;
  };
}

export interface CreateProjectData {
  name: string;
  description?: string;
  ai_chat_enabled: boolean;
  save_files_on_server: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sql_query?: string;
  table_data?: any[];
}

/**
 * Get Firebase ID token for authentication
 */
async function getAuthToken(): Promise<string> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('Not authenticated');
  }
  return await user.getIdToken();
}

/**
 * Make authenticated API request
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || 'Request failed');
  }

  return response.json();
}

// ============================================================================
// PROJECT API
// ============================================================================

export const projectsApi = {
  /**
   * List all projects for authenticated user
   */
  async list(status?: string): Promise<{ projects: Project[]; total: number }> {
    const params = status ? `?status=${status}` : '';
    return apiRequest(`/projects${params}`);
  },

  /**
   * Create a new project
   */
  async create(data: CreateProjectData): Promise<{ success: boolean; project: Project }> {
    return apiRequest('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get project details
   */
  async get(projectId: string): Promise<Project> {
    return apiRequest(`/projects/${projectId}`);
  },

  /**
   * Update project
   */
  async update(
    projectId: string,
    data: Partial<CreateProjectData>
  ): Promise<{ success: boolean; project: Project }> {
    return apiRequest(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete project
   */
  async delete(projectId: string): Promise<{ success: boolean }> {
    return apiRequest(`/projects/${projectId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get upload status for a project
   */
  async getUploadStatus(projectId: string): Promise<{
    upload_completed: boolean;
    validation_status: boolean | null;
    has_errors: boolean;
    error_summary: any;
    validation_params: any;
  }> {
    return apiRequest(`/projects/${projectId}/upload-status`);
  },

  /**
   * Upload CSV file to project
   */
  async uploadCSV(
    projectId: string,
    file: File,
    params: {
      start_date: string;
      end_date: string;
      date_format?: string;
      flight_starts_with?: string;
      fuel_method?: string;
    }
  ): Promise<{ success: boolean; is_valid: boolean; filename: string; error_summary?: any }> {
    const token = await getAuthToken();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('start_date', params.start_date);
    formData.append('end_date', params.end_date);
    formData.append('date_format', params.date_format || 'DMY');
    formData.append('flight_starts_with', params.flight_starts_with || '');
    formData.append('fuel_method', params.fuel_method || 'Block Off - Block On');

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new Error(error.error || 'Upload failed');
    }

    return response.json();
  },

  /**
   * Download CSV file (clean or errors)
   */
  async downloadCSV(projectId: string, type: 'clean' | 'errors'): Promise<Blob> {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/download/${type}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Download failed');
    }

    return response.blob();
  },

  /**
   * Generate CORSIA report
   */
  async generateReport(
    projectId: string,
    flightPrefix?: string
  ): Promise<Blob> {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/report`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ flight_starts_with: flightPrefix || '' }),
    });

    if (!response.ok) {
      throw new Error('Report generation failed');
    }

    return response.blob();
  },
};

// ============================================================================
// CHAT API
// ============================================================================

export const chatApi = {
  /**
   * Initialize chat session for project
   */
  async initialize(projectId: string): Promise<{ success: boolean; session_id: string }> {
    return apiRequest(`/projects/${projectId}/chat/initialize`, {
      method: 'POST',
    });
  },

  /**
   * Send chat query
   */
  async query(
    projectId: string,
    query: string,
    sessionId?: string
  ): Promise<{
    status: string;
    response: string;
    sql_query?: string;
    table_data?: any[];
  }> {
    return apiRequest(`/projects/${projectId}/chat/query`, {
      method: 'POST',
      body: JSON.stringify({ query, session_id: sessionId }),
    });
  },
};

// ============================================================================
// AUTH API
// ============================================================================

export const authApi = {
  /**
   * Verify Firebase token with backend
   */
  async verify(): Promise<{ success: boolean; user: any }> {
    return apiRequest('/auth/verify', { method: 'POST' });
  },

  /**
   * Get current user info
   */
  async getMe(): Promise<any> {
    return apiRequest('/auth/me');
  },
};

export default {
  projects: projectsApi,
  chat: chatApi,
  auth: authApi,
};
