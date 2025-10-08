/**
 * Validation Service - Handles CSV validation and error correction
 */

import { auth } from './firebase';
import type {
  ValidationParams,
  ValidationResult,
  ValidationErrorData,
  ColumnMapping,
} from '@/types/validation';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5002/api';

async function getAuthToken(): Promise<string> {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('Not authenticated');
  }
  return await user.getIdToken();
}

export const validationService = {
  /**
   * Upload and validate CSV file for a project with all parameters
   */
  async uploadFile(
    projectId: string,
    file: File,
    params: {
      start_date: string;
      end_date: string;
      date_format?: string;
      flight_starts_with?: string;
      fuel_method?: string;
    },
    onProgress?: (progress: number) => void
  ): Promise<{ success: boolean; is_valid: boolean; filename: string }> {
    const token = await getAuthToken();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('start_date', params.start_date);
    formData.append('end_date', params.end_date);
    formData.append('date_format', params.date_format || 'DMY');
    formData.append('flight_starts_with', params.flight_starts_with || '');
    formData.append('fuel_method', params.fuel_method || 'Block Off - Block On');

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.error || 'Upload failed'));
          } catch {
            reject(new Error('Upload failed'));
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', `${API_BASE_URL}/projects/${projectId}/upload`);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.send(formData);
    });
  },

  /**
   * Get CSV columns by reading the file locally (client-side)
   */
  async getCSVColumns(file: File): Promise<string[]> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        const text = e.target?.result as string;
        const firstLine = text.split('\n')[0];
        const columns = firstLine.split(',').map(col => col.trim().replace(/^"|"$/g, ''));
        resolve(columns);
      };

      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };

      reader.readAsText(file);
    });
  },

  /**
   * Validate uploaded CSV with parameters
   */
  async validateFile(
    projectId: string,
    params: ValidationParams
  ): Promise<ValidationResult> {
    const token = await getAuthToken();

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/validate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Validation failed' }));
      throw new Error(error.error || 'Validation failed');
    }

    return response.json();
  },

  /**
   * Get validation errors for a project
   */
  async getErrors(projectId: string): Promise<ValidationErrorData> {
    const token = await getAuthToken();

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/errors`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch errors');
    }

    return response.json();
  },

  /**
   * Save error corrections
   */
  async saveCorrections(
    projectId: string,
    corrections: { [rowIdx: number]: any }
  ): Promise<{ success: boolean; updated_count: number }> {
    const token = await getAuthToken();

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/corrections`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ corrections }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to save corrections' }));
      throw new Error(error.error || 'Failed to save corrections');
    }

    return response.json();
  },

  /**
   * Download CSV file (clean or errors)
   */
  async downloadCSV(
    projectId: string,
    type: 'clean' | 'errors'
  ): Promise<Blob> {
    const token = await getAuthToken();

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/download/${type}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to download ${type} CSV`);
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
      const error = await response.json().catch(() => ({ error: 'Report generation failed' }));
      throw new Error(error.error || 'Report generation failed');
    }

    return response.blob();
  },

  /**
   * Get column mapping suggestions based on CSV headers
   */
  getSuggestedMapping(csvColumns: string[]): ColumnMapping {
    const mapping: ColumnMapping = {};
    const requiredColumns = [
      'Flight Number',
      'Departure Airport ICAO',
      'Arrival Airport ICAO',
      'Departure Date',
      'Fuel Uplift',
      'Block-Off',
      'Block-On',
    ];

    // Simple fuzzy matching for common column names
    const fuzzyMatch = (required: string, csv: string): number => {
      const r = required.toLowerCase().replace(/[^a-z0-9]/g, '');
      const c = csv.toLowerCase().replace(/[^a-z0-9]/g, '');

      if (r === c) return 100;
      if (c.includes(r) || r.includes(c)) return 80;

      // Check for keyword matches
      const keywords: { [key: string]: string[] } = {
        'flight number': ['flight', 'flt', 'number', 'flightno'],
        'departure airport icao': ['departure', 'dept', 'origin', 'from', 'icao'],
        'arrival airport icao': ['arrival', 'arr', 'destination', 'dest', 'to', 'icao'],
        'departure date': ['date', 'departure', 'dept'],
        'fuel uplift': ['fuel', 'uplift'],
        'blockoff': ['blockoff', 'block', 'off'],
        'blockon': ['blockon', 'block', 'on'],
      };

      const reqKeywords = keywords[r] || [];
      const matchCount = reqKeywords.filter(kw => c.includes(kw)).length;

      return matchCount > 0 ? matchCount * 20 : 0;
    };

    requiredColumns.forEach(required => {
      let bestMatch = '';
      let bestScore = 0;

      csvColumns.forEach(csv => {
        const score = fuzzyMatch(required, csv);
        if (score > bestScore) {
          bestScore = score;
          bestMatch = csv;
        }
      });

      if (bestScore >= 50) {
        mapping[required] = bestMatch;
      }
    });

    return mapping;
  },
};

export default validationService;
