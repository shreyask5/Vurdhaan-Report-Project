// Validation Service - Updated for app5.py API
// Base URL: https://tools.vurdhaan.com/api
// Requires Firebase authentication

import {
  ValidationFormData,
  ErrorData,
  Correction,
  UploadResponse,
  ErrorMetadata,
  PaginatedErrorData
} from '../types/validation';
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

export const validationService = {
  /**
   * Upload CSV file with validation parameters
   * POST /api/projects/{project_id}/upload
   * From app5.py:237-286
   */
  async uploadFile(
    projectId: string,
    file: File,
    params: ValidationFormData
  ): Promise<UploadResponse> {
    const token = await getAuthToken();
    const formData = new FormData();
    formData.append('file', file);

    // Extract dates from monitoring year
    const year = params.monitoring_year;
    formData.append('start_date', `${year}-01-01`);
    formData.append('end_date', `${year}-12-31`);
    formData.append('date_format', params.date_format);
    formData.append('flight_starts_with', params.flight_starts_with);
    formData.append('fuel_method', params.fuel_method);

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new Error(error.error || 'Failed to upload file');
    }

    return response.json();
  },

  /**
   * Download clean CSV
   * GET /api/projects/{project_id}/download/clean
   * From app5.py:398-415
   */
  async downloadClean(projectId: string): Promise<void> {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/download/clean`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to download clean CSV');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `clean_data_${projectId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Download errors CSV
   * GET /api/projects/{project_id}/download/errors
   * From app5.py:398-415
   */
  async downloadErrors(projectId: string): Promise<void> {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/download/errors`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to download errors CSV');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `errors_data_${projectId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Generate CORSIA report
   * POST /api/projects/{project_id}/report
   * From app5.py:374-396
   */
  async generateReport(projectId: string, flightPrefix: string = ''): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/report`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ flight_starts_with: flightPrefix })
    });

    if (!response.ok) {
      throw new Error('Failed to generate report');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `report_${projectId}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Initialize chat session for project
   * POST /api/projects/{project_id}/chat/initialize
   * From app5.py:292-328
   */
  async initializeChatSession(projectId: string): Promise<{ session_id: string; database_info: any }> {
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
   * Get project details
   * GET /api/projects/{project_id}
   * From app5.py:184-204
   */
  async getProject(projectId: string): Promise<any> {
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
   * Fetch errors for a file/project
   * GET /api/projects/{project_id}/errors (or similar endpoint)
   * With decompression support from index4.html:2095-2224
   */
  // REMOVED: fetchErrors() - replaced with pagination-based fetchErrorMetadata() and fetchCategoryPage()

  /**
   * Save corrections
   * POST /api/projects/{project_id}/corrections
   */
  async saveCorrections(projectId: string, corrections: Correction[]): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/corrections`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ corrections })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to save corrections' }));
      throw new Error(error.error || 'Failed to save corrections');
    }
  },

  /**
   * Ignore remaining errors
   * POST /api/projects/{project_id}/ignore-errors
   */
  async ignoreErrors(projectId: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/ignore-errors`, {
      method: 'POST',
      headers
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to ignore errors' }));
      throw new Error(error.error || 'Failed to ignore errors');
    }
  },

  /**
   * Re-validate and process again
   * POST /api/projects/{project_id}/revalidate
   */
  async revalidate(projectId: string): Promise<void> {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/revalidate`, {
      method: 'POST',
      headers
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to re-validate' }));
      throw new Error(error.error || 'Failed to re-validate');
    }
  },

  // ========================================================================
  // PAGINATED ERROR REPORTING API
  // ========================================================================

  /**
   * Fetch error metadata including all categories and page counts
   * GET /api/projects/{project_id}/errors/metadata
   * From app5.py:709-758
   */
  async fetchErrorMetadata(projectId: string): Promise<ErrorMetadata> {
    console.log('[VALIDATION SERVICE] Fetching error metadata for project:', projectId);
    const token = await getAuthToken();
    const url = `${API_BASE_URL}/projects/${projectId}/errors/metadata`;
    console.log('[VALIDATION SERVICE] Metadata URL:', url);

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    console.log('[VALIDATION SERVICE] Metadata response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[VALIDATION SERVICE] Metadata error response:', errorText);
      throw new Error(`Failed to fetch error metadata: ${response.status} ${errorText}`);
    }

    const metadata = await response.json();
    console.log('[VALIDATION SERVICE] Error metadata:', {
      totalErrors: metadata.total_errors,
      errorRows: metadata.error_rows,
      categoriesCount: metadata.error_categories,
      categories: metadata.categories?.map((c: any) => `${c.name}(${c.total_pages}p)`)
    });

    return metadata;
  },

  /**
   * Fetch a specific page for a specific error category
   * GET /api/projects/{project_id}/errors?category={category}&page={page}
   * From app5.py:761-855
   */
  async fetchCategoryPage(
    projectId: string,
    category: string,
    page: number = 1
  ): Promise<PaginatedErrorData> {
    console.log('[VALIDATION SERVICE] Fetching category page:', { projectId, category, page });
    const token = await getAuthToken();
    const url = `${API_BASE_URL}/projects/${projectId}/errors?category=${encodeURIComponent(category)}&page=${page}`;
    console.log('[VALIDATION SERVICE] Category page URL:', url);

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    console.log('[VALIDATION SERVICE] Category page response status:', response.status);
    console.log('[VALIDATION SERVICE] Category page response headers:', {
      contentType: response.headers.get('content-type'),
      compression: response.headers.get('x-compression'),
      contentLength: response.headers.get('content-length')
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[VALIDATION SERVICE] Category page error response:', errorText);
      throw new Error(`Failed to fetch category page: ${response.status} ${errorText}`);
    }

    // Check response headers to determine if data is compressed
    const contentType = response.headers.get('content-type');
    const compressionType = response.headers.get('x-compression');

    let data: PaginatedErrorData;

    if (compressionType === 'lzstring' || contentType === 'text/plain') {
      console.log('[VALIDATION SERVICE] Handling compressed paginated data');
      // Handle LZ-String compressed data
      const { decompressLZStringPaginatedPage } = await import('../utils/compression');
      const compressedData = await response.text();
      data = await decompressLZStringPaginatedPage(compressedData);
    } else {
      console.log('[VALIDATION SERVICE] Handling JSON paginated data');
      // Handle regular JSON
      data = await response.json();
    }

    console.log('[VALIDATION SERVICE] Parsed paginated data:', {
      category: data.category_name,
      page: data.page,
      totalPages: data.total_pages,
      errorsOnPage: data.errors_on_page,
      hasRowsData: !!data.rows_data,
      rowsDataKeys: data.rows_data ? Object.keys(data.rows_data).length : 0,
      errorGroups: data.error_groups?.length || 0
    });

    return data;
  }
};
