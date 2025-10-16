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
      // Don't wait for extraction - it runs in background
      setProcessingStatus('done');
      if (onComplete) {
        onComplete(); // Allow user to proceed immediately
      }
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
          Upload your monitoring plan document. We'll extract key information automatically in the background.
        </p>
        <p className="text-blue-700 bg-blue-50 border border-blue-200 rounded mt-3 p-3 text-sm">
          ℹ️ Extraction runs in the background (up to 10 minutes). You can proceed to the next steps while it processes.
        </p>
      </div>

      {/* Processing Status */}
      {isUploading && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-4"></div>
          <h3 className="text-xl font-semibold text-blue-700 mb-2">
            Uploading monitoring plan...
          </h3>
          <p className="text-sm text-blue-600">
            Please wait a moment...
          </p>
        </div>
      )}

      {/* Error Status */}
      {processingStatus === 'error' && (
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-4xl">❌</div>
            <div>
              <h3 className="text-xl font-semibold text-red-700">Upload Failed</h3>
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

      {/* Success Message */}
      {processingStatus === 'done' && (
        <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <div className="text-4xl">✅</div>
            <div>
              <h3 className="text-xl font-semibold text-green-700">Upload Successful!</h3>
              <p className="text-sm text-green-600">
                Your monitoring plan is being processed in the background. You can proceed to the next step.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* File Upload Area */}
      {!isUploading && processingStatus !== 'error' && processingStatus !== 'done' && (
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
                  {isUploading ? 'Uploading...' : 'Upload & Process'}
                </button>
              )}
            </div>
          </div>
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
        {processingStatus === 'done' && onComplete && (
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
