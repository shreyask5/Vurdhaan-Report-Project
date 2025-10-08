// Validation Service
// Handles all CSV validation API calls
// Based on index4.html endpoints

import {
  ValidationFormData,
  ErrorData,
  Correction,
  UploadResponse,
  CompressedErrorResponse
} from '../types/validation';
import { decompressLZStringErrorReport, isCompressedResponse } from '../utils/compression';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const validationService = {
  /**
   * Upload CSV file with validation parameters
   * POST /upload
   * From index4.html:2098-2165
   */
  async uploadFile(
    file: File,
    params: ValidationFormData
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('monitoring_year', params.monitoring_year);
    formData.append('date_format', params.date_format);
    formData.append('flight_starts_with', params.flight_starts_with);
    formData.append('column_mapping', JSON.stringify(params.column_mapping));
    formData.append('fuel_method', params.fuel_method);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || 'Failed to upload file');
    }

    return response.json();
  },

  /**
   * Fetch errors for a file
   * GET /errors/{file_id}
   * From index4.html:2167-2224
   * Handles both compressed and uncompressed responses
   */
  async fetchErrors(fileId: string): Promise<ErrorData> {
    const response = await fetch(`${API_BASE_URL}/errors/${fileId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch errors');
    }

    const data = await response.json();

    // Check if response is compressed
    if (isCompressedResponse(data)) {
      console.log('📦 Compressed response detected, decompressing...');
      return await decompressLZStringErrorReport((data as CompressedErrorResponse).compressed_data);
    }

    return data as ErrorData;
  },

  /**
   * Save corrections for errors
   * PUT /upload/{file_id}
   * From index4.html:2841-2871
   */
  async saveCorrections(
    fileId: string,
    corrections: Correction[]
  ): Promise<UploadResponse> {
    const response = await fetch(`${API_BASE_URL}/upload/${fileId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ corrections })
    });

    if (!response.ok) {
      throw new Error('Failed to save corrections');
    }

    return response.json();
  },

  /**
   * Ignore errors and proceed
   * PUT /upload/{file_id}
   * From index4.html:2873-2897
   */
  async ignoreErrors(fileId: string): Promise<UploadResponse> {
    const response = await fetch(`${API_BASE_URL}/upload/${fileId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ignore_errors: true })
    });

    if (!response.ok) {
      throw new Error('Failed to ignore errors');
    }

    return response.json();
  },

  /**
   * Revalidate the file
   * PUT /upload/{file_id}
   * From index4.html:3086-3124
   */
  async revalidate(fileId: string): Promise<UploadResponse> {
    const response = await fetch(`${API_BASE_URL}/upload/${fileId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ revalidate: true })
    });

    if (!response.ok) {
      throw new Error('Failed to revalidate');
    }

    return response.json();
  },

  /**
   * Download clean CSV
   * GET /download/{file_id}/clean
   * From index4.html:3006-3025
   */
  async downloadClean(fileId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/download/${fileId}/clean`);

    if (!response.ok) {
      throw new Error('Failed to download clean CSV');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `clean_flights_${fileId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Download errors CSV
   * GET /download/{file_id}/errors
   * From index4.html:3027-3046
   */
  async downloadErrors(fileId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/download/${fileId}/errors`);

    if (!response.ok) {
      throw new Error('Failed to download errors CSV');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `error_flights_${fileId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Generate CORSIA report
   * POST /report/{file_id}
   * From index4.html:3048-3084
   */
  async generateReport(fileId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/report/${fileId}`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error('Failed to generate report');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'template_filled.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },

  /**
   * Open chat session from validated file
   * POST /open-chat/{file_id}
   * From index4.html:2899-3003
   */
  async openChatSession(fileId: string): Promise<{ chat_url: string; session_id: string }> {
    const response = await fetch(`${API_BASE_URL}/open-chat/${fileId}`, {
      method: 'POST'
    });

    if (!response.ok) {
      throw new Error('Failed to create chat session');
    }

    return response.json();
  }
};
