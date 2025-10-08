// File Upload Component with drag & drop
// Based on index4.html:1986-2096

import React, { useState, useRef } from 'react';
import { isCSVFile, formatFileSize } from '../../utils/csv';

interface FileUploadSectionProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSize?: number; // in bytes
  label?: string;
}

export const FileUploadSection: React.FC<FileUploadSectionProps> = ({
  onFileSelect,
  accept = '.csv',
  maxSize = 50 * 1024 * 1024, // 50MB default
  label = 'Upload CSV File'
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // From index4.html:1995-2011
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  // From index4.html:2013-2032
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  // From index4.html:2033-2064
  const handleFileSelection = (file: File) => {
    console.log('📁 File selected:', file.name, formatFileSize(file.size));

    // Validate file type
    if (!isCSVFile(file)) {
      alert('Please select a CSV file');
      return;
    }

    // Validate file size
    if (file.size > maxSize) {
      alert(`File size exceeds maximum allowed size of ${formatFileSize(maxSize)}`);
      return;
    }

    // Validate file is not empty
    if (file.size === 0) {
      alert('Selected file is empty');
      return;
    }

    setSelectedFile(file);
    onFileSelect(file);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelection(files[0]);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="file-upload-section">
      {/* Drag & Drop Zone - From index4.html:142-201 */}
      <div
        className={`dropzone ${isDragging ? 'dragover' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        <div className="dropzone-content">
          <svg
            className="upload-icon"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            width="48"
            height="48"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="dropzone-text">
            {selectedFile ? (
              <>
                <strong>{selectedFile.name}</strong>
                <br />
                <span className="text-sm text-gray-500">
                  {formatFileSize(selectedFile.size)}
                </span>
              </>
            ) : (
              <>
                Drag and drop your CSV file here or click to browse
                <br />
                <span className="text-sm text-gray-500">
                  Maximum file size: {formatFileSize(maxSize)}
                </span>
              </>
            )}
          </p>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileInputChange}
        className="hidden"
      />

      <style jsx>{`
        .file-upload-section {
          margin-bottom: 2rem;
        }

        .dropzone {
          border: 3px dashed #cbd5e1;
          border-radius: 1rem;
          padding: 3rem 2rem;
          text-align: center;
          background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
          transition: all 0.3s ease;
          cursor: pointer;
          min-height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .dropzone:hover {
          border-color: #6366f1;
          background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
          transform: translateY(-2px);
        }

        .dropzone.dragover {
          border-color: #4f46e5;
          background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
          transform: scale(1.02);
        }

        .dropzone-content {
          pointer-events: none;
        }

        .upload-icon {
          margin: 0 auto 1rem;
          color: #6366f1;
        }

        .dropzone-text {
          font-size: 1rem;
          color: #475569;
          margin: 0;
          line-height: 1.6;
        }

        .dropzone.dragover .dropzone-text {
          color: #4f46e5;
          font-weight: 600;
        }
      `}</style>
    </div>
  );
};
