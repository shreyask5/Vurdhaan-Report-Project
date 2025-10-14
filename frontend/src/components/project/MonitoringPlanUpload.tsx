import React, { useState, useCallback } from 'react';
import { MonitoringPlanData } from '../../types/validation';

interface MonitoringPlanUploadProps {
  projectId: string;
  onUpload: (file: File) => Promise<void>;
  extractedData?: MonitoringPlanData | null;
  onBack: () => void;
  onComplete?: () => void;
}

export const MonitoringPlanUpload: React.FC<MonitoringPlanUploadProps> = ({
  projectId,
  onUpload,
  extractedData,
  onBack,
  onComplete
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<'queued' | 'running' | 'done' | 'error' | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setProcessingStatus(null);
    setErrorMessage(null);

    try {
      await onUpload(selectedFile);
      setProcessingStatus('done');
    } catch (error) {
      console.error('Upload failed:', error);
      setProcessingStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to upload monitoring plan');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRetry = () => {
    setProcessingStatus(null);
    setErrorMessage(null);
    setSelectedFile(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold text-gray-700 mb-2">
          Upload Monitoring Plan
        </h2>
        <p className="text-gray-600">
          Upload your monitoring plan document. We'll extract key information automatically.
        </p>
        <p className="text-yellow-700 bg-yellow-50 border border-yellow-200 rounded mt-3 p-3 text-sm">
          ⚠️ Extraction may take up to 10 minutes. Please wait for processing to complete before proceeding.
        </p>
      </div>

      {/* Processing Status */}
      {isUploading && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-4"></div>
          <h3 className="text-xl font-semibold text-blue-700 mb-2">
            Extracting monitoring plan data...
          </h3>
          <p className="text-sm text-blue-600">
            This may take up to 10 minutes. Please don't close this window.
          </p>
          <div className="mt-4 space-y-2 text-sm text-blue-600">
            <p>💡 Tip: We're analyzing your document using AI to extract key information</p>
            <p>💡 Tip: Longer documents may take more time to process</p>
          </div>
        </div>
      )}

      {/* Error Status */}
      {processingStatus === 'error' && (
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-4xl">❌</div>
            <div>
              <h3 className="text-xl font-semibold text-red-700">Extraction Failed</h3>
              <p className="text-sm text-red-600">{errorMessage}</p>
            </div>
          </div>
          <button
            onClick={handleRetry}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            Try Again
          </button>
        </div>
      )}

      {/* File Upload Area */}
      {!extractedData && !isUploading && processingStatus !== 'error' && (
        <div
          className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
            dragActive
              ? 'border-primary bg-primary bg-opacity-5'
              : 'border-gray-300 hover:border-primary'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="monitoring-plan-upload"
            className="hidden"
            accept=".pdf,.xlsx,.xls,.csv,.png,.jpg,.jpeg,.gif,.bmp,.tiff,.webp"
            onChange={handleFileChange}
            disabled={isUploading}
          />

          <div className="space-y-4">
            <div className="text-6xl">📄</div>
            <div>
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                {selectedFile ? selectedFile.name : 'Drop your monitoring plan here'}
              </h3>
              <p className="text-sm text-gray-500">
                Supported formats: PDF, Excel, CSV, Images (PNG, JPG, etc.)
              </p>
              <p className="text-sm text-gray-500 mt-1">Maximum file size: 50MB</p>
            </div>

            <div className="flex gap-3 justify-center">
              <label
                htmlFor="monitoring-plan-upload"
                className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark cursor-pointer transition"
              >
                Choose File
              </label>
              {selectedFile && (
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    isUploading
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-success text-white hover:bg-success-dark'
                  }`}
                >
                  {isUploading ? 'Processing...' : 'Upload & Process'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Extracted Data Display */}
      {extractedData && (
        <div className="bg-white rounded-xl border-2 border-success p-6 space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b">
            <div className="text-4xl">✅</div>
            <div>
              <h3 className="text-xl font-semibold text-success">
                Monitoring Plan Analyzed Successfully
              </h3>
              <p className="text-sm text-gray-600">
                Key information has been extracted from your document
              </p>
            </div>
          </div>

          {/* Basic Info */}
          {extractedData.basic_info && Object.keys(extractedData.basic_info).length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">📋 Basic Information</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                {extractedData.basic_info.airline_name && (
                  <div>
                    <span className="text-gray-600">Airline:</span>{' '}
                    <span className="font-medium">{extractedData.basic_info.airline_name}</span>
                  </div>
                )}
                {extractedData.basic_info.version && (
                  <div>
                    <span className="text-gray-600">Version:</span>{' '}
                    <span className="font-medium">{extractedData.basic_info.version}</span>
                  </div>
                )}
                {extractedData.basic_info.date && (
                  <div>
                    <span className="text-gray-600">Date:</span>{' '}
                    <span className="font-medium">{extractedData.basic_info.date}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Fuel Data Collection */}
          {extractedData.fuel_data_collection && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">⛽ Fuel Data Collection</h4>
              <div className="text-sm space-y-2">
                {extractedData.fuel_data_collection.collection_method && (
                  <div>
                    <span className="text-gray-600">Method:</span>{' '}
                    <span className="font-medium capitalize">
                      {extractedData.fuel_data_collection.collection_method}
                    </span>
                  </div>
                )}
                {extractedData.primary_data_source?.is_automatic !== undefined && (
                  <div>
                    <span className="text-gray-600">Primary Source:</span>{' '}
                    <span className="font-medium">
                      {extractedData.primary_data_source.is_automatic ? 'Automatic' : 'Manual'}
                    </span>
                  </div>
                )}
                {extractedData.secondary_source?.uses_paper_logs !== undefined && (
                  <div>
                    <span className="text-gray-600">Paper Logs (Secondary):</span>{' '}
                    <span className="font-medium">
                      {extractedData.secondary_source.uses_paper_logs ? 'Yes' : 'No'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Geographical Presence */}
          {extractedData.geographical_presence && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">🌍 Geographical Presence</h4>
              <div className="text-sm space-y-2">
                {extractedData.geographical_presence.is_eu_based !== undefined && (
                  <div>
                    <span className="text-gray-600">EU-based:</span>{' '}
                    <span className="font-medium">
                      {extractedData.geographical_presence.is_eu_based ? 'Yes' : 'No'}
                    </span>
                  </div>
                )}
                {extractedData.geographical_presence.is_non_eu_based !== undefined && (
                  <div>
                    <span className="text-gray-600">Non-EU based:</span>{' '}
                    <span className="font-medium">
                      {extractedData.geographical_presence.is_non_eu_based ? 'Yes' : 'No'}
                    </span>
                  </div>
                )}
                {extractedData.geographical_presence.scheme_priority && (
                  <div className="mt-3">
                    <div className="text-gray-600 mb-2">Scheme Priority:</div>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(extractedData.geographical_presence.scheme_priority).map(
                        ([scheme, priority]) => (
                          <span
                            key={scheme}
                            className={`px-3 py-1 rounded-full text-xs font-medium ${
                              priority === 'high'
                                ? 'bg-red-100 text-red-700'
                                : priority === 'standard'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {scheme}: {priority}
                          </span>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Monitoring Plan Processes */}
          {extractedData.monitoring_plan_processes &&
           Object.keys(extractedData.monitoring_plan_processes).length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">📊 Monitoring Plan Processes</h4>
              <div className="text-sm space-y-2">
                {Object.entries(extractedData.monitoring_plan_processes).map(
                  ([scheme, process]) =>
                    process && (
                      <div key={scheme} className="p-3 bg-gray-50 rounded">
                        <div className="font-medium text-gray-700">{scheme}:</div>
                        <div className="text-gray-600 mt-1">{process}</div>
                      </div>
                    )
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          disabled={isUploading}
          className={`px-6 py-2 border-2 border-gray-300 rounded-lg transition ${
            isUploading
              ? 'text-gray-400 cursor-not-allowed'
              : 'text-gray-700 hover:bg-gray-50'
          }`}
        >
          Back to Scheme
        </button>
        {extractedData && !isUploading && (
          <button
            onClick={onComplete}
            className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition"
          >
            Continue to Parameters →
          </button>
        )}
      </div>
    </div>
  );
};
