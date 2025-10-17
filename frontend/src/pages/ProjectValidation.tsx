import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useValidation } from '../contexts/ValidationContext';
import { ErrorSummary } from '../components/project/ErrorSummary';
import { ErrorCategory } from '../components/project/ErrorCategory';
import { FUEL_METHOD_COLUMNS } from '../types/validation';
import { validationService } from '../services/validation';
import { ProjectHeader } from '../components/layout/ProjectHeader';

const ProjectValidation: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const {
    fileId,
    errorData,
    selectedFuelMethod,
    corrections,
    currentStep,
    isLoading,
    fetchErrors,
    saveCorrections,
    ignoreErrors,
    addCorrection,
    reset
  } = useValidation();

  useEffect(() => {
    if (fileId && !errorData && currentStep === 'validation') {
      fetchErrors();
    }
  }, [fileId, errorData, currentStep]);

  // Redirect if on success step
  useEffect(() => {
    if (currentStep === 'success') {
      // Show success state instead
    }
  }, [currentStep]);

  const handleOpenChat = async () => {
    if (!fileId) return;
    try {
      const { chat_url } = await validationService.openChatSession(fileId);
      const popup = window.open(chat_url, '_blank', 'width=1200,height=800');

      if (!popup || popup.closed || typeof popup.closed === 'undefined') {
        const userChoice = confirm(
          'Popup was blocked. Click OK to open chat in this tab, or Cancel to copy the URL.'
        );
        if (userChoice) {
          window.location.href = chat_url;
        } else {
          navigator.clipboard.writeText(chat_url);
          alert('Chat URL copied to clipboard!');
        }
      }
    } catch (error) {
      alert('Failed to open chat session');
    }
  };

  const handleDownloadClean = async () => {
    if (!projectId) return;
    try {
      await validationService.downloadClean(projectId);
    } catch (error) {
      alert('Failed to download clean CSV');
    }
  };

  const handleDownloadErrors = async () => {
    if (!projectId) return;
    try {
      await validationService.downloadErrors(projectId);
    } catch (error) {
      alert('Failed to download errors CSV');
    }
  };

  const handleGenerateReport = async () => {
    if (!projectId) return;
    try {
      await validationService.generateReport(projectId);
      setTimeout(() => {
        reset();
        navigate('/dashboard');
      }, 2000);
    } catch (error) {
      alert('Failed to generate report');
    }
  };

  const handleSaveCorrections = async () => {
    if (!projectId) return;
    try {
      await saveCorrections(projectId);
      alert('✅ Corrections saved successfully!');
    } catch (error) {
      alert('❌ Failed to save corrections');
    }
  };

  const handleIgnoreErrors = async () => {
    if (!projectId) return;
    const confirmed = confirm('Are you sure you want to ignore all errors and proceed?');
    if (confirmed) {
      try {
        await ignoreErrors(projectId);
        // Navigate to monitoring plan review after ignoring errors
        navigate(`/projects/${projectId}/monitoring-plan-review`);
      } catch (error) {
        alert('❌ Failed to ignore errors');
      }
    }
  };

  const handleReset = () => {
    const confirmed = confirm('Are you sure you want to start over? All progress will be lost.');
    if (confirmed) {
      reset();
      navigate(`/projects/${projectId}/upload`);
    }
  };

  const columnOrder = selectedFuelMethod ? FUEL_METHOD_COLUMNS[selectedFuelMethod] : [];

  // Success state
  if (currentStep === 'success') {
    return (
      <div className="min-h-screen bg-gradient-radial flex items-center justify-center">
        <div className="bg-white rounded-2xl p-12 shadow-xl text-center max-w-2xl">
          <div className="text-6xl mb-6">✅</div>
          <h1 className="text-3xl font-bold text-gray-800 mb-4">Validation Successful!</h1>
          <p className="text-gray-600 mb-8">
            Your CSV file has been validated and is ready for reporting.
          </p>

          <div className="flex flex-col gap-4">
            <button onClick={handleGenerateReport} className="btn-primary py-4 text-lg">
              Generate CORSIA Report
            </button>
            <button onClick={handleDownloadClean} className="btn-secondary">
              Download Clean CSV
            </button>
            <button onClick={handleOpenChat} className="btn-success">
              Open AI Chat Assistant
            </button>
            <button onClick={handleReset} className="btn-secondary">
              Upload Another File
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Loading or no data state
  if (isLoading || !errorData) {
    return (
      <div className="min-h-screen bg-gradient-radial flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 shadow-xl text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-4"></div>
          <p className="text-lg font-semibold text-gray-700">Loading validation results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-radial">
      <ProjectHeader />
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Validation Results</h1>
          <p className="text-gray-600 mt-2">
            Review and correct errors found in your CSV file
          </p>
        </div>

        {/* Error Summary */}
        <ErrorSummary errorData={errorData} />

        {/* Actions Bar */}
        <div className="bg-white rounded-xl p-6 shadow-card mb-6">
          <h3 className="font-semibold text-gray-700 mb-4">Actions</h3>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleSaveCorrections}
              disabled={corrections.size === 0 || isLoading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              💾 Save Corrections ({corrections.size})
            </button>
            <button
              onClick={handleIgnoreErrors}
              disabled={isLoading}
              className="btn-warning disabled:opacity-50"
            >
              ⚠️ Ignore Errors & Continue
            </button>
            <button
              onClick={handleDownloadClean}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50"
            >
              📥 Download Clean CSV
            </button>
            <button
              onClick={handleDownloadErrors}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50"
            >
              📥 Download Errors CSV
            </button>
            <button
              onClick={handleOpenChat}
              disabled={isLoading}
              className="btn-success disabled:opacity-50"
            >
              💬 Open AI Chat
            </button>
            <button
              onClick={handleReset}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50"
            >
              🔄 Start Over
            </button>
          </div>
        </div>

        {/* Next Step Button */}
        <div className="bg-white rounded-xl p-6 shadow-card mb-6 flex justify-end">
          <button
            onClick={() => navigate(`/projects/${projectId}/monitoring-plan-review`)}
            disabled={isLoading}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed px-8 py-3"
          >
            Review Monitoring Plan →
          </button>
        </div>

        {/* Error Categories */}
        <div className="errors-container space-y-4">
          {errorData.categories.map((category, index) => (
            <ErrorCategory
              key={`${category.name}-${index}`}
              category={category}
              columnOrder={columnOrder}
              rowsData={errorData.rows_data}
              onCorrection={addCorrection}
            />
          ))}
        </div>
      </div>

      <style jsx>{`
        .btn-primary,
        .btn-secondary,
        .btn-success,
        .btn-warning {
          padding: 0.75rem 1.5rem;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s ease;
          border: none;
        }

        .btn-primary {
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
          transform: translateY(-2px);
        }

        .btn-secondary {
          background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
          color: white;
        }

        .btn-secondary:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(100, 116, 139, 0.3);
          transform: translateY(-2px);
        }

        .btn-success {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
        }

        .btn-success:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
          transform: translateY(-2px);
        }

        .btn-warning {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          color: white;
        }

        .btn-warning:hover:not(:disabled) {
          box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.3);
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
};

export default ProjectValidation;
