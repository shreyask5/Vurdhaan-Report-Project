import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useValidation } from '../contexts/ValidationContext';
import { ErrorSummary } from '../components/project/ErrorSummary';
import { ErrorCategory } from '../components/project/ErrorCategory';
import { ActionButtons } from '../components/project/ActionButtons';
import { SuccessSection } from '../components/project/SuccessSection';
import { LoadingSection } from '../components/project/LoadingSection';
import { FUEL_METHOD_COLUMNS } from '../types/validation';
import { validationService } from '../services/validation';
import { ProjectHeader } from '../components/layout/ProjectHeader';
import { createSequenceSummary, processSequenceGroups } from '../utils/errorProcessing';

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

  const [loadingMessage, setLoadingMessage] = useState('Loading validation results...');
  const [sequenceSummaryItems, setSequenceSummaryItems] = useState<any[]>([]);
  const hasFetchedRef = React.useRef(false);

  // Fetch errors when component mounts
  React.useEffect(() => {
    if (projectId && !hasFetchedRef.current) {
      hasFetchedRef.current = true;
      console.log('[PROJECT VALIDATION] Fetching errors for project:', projectId);
      fetchErrors(projectId).catch(error => {
        console.error('[PROJECT VALIDATION] Failed to fetch errors:', error);
        setLoadingMessage('Failed to load validation results');
      });
    }
  }, [projectId]);

  // Process sequence errors for final summary
  useEffect(() => {
    if (errorData && errorData.categories) {
      const allSequenceErrors = new Map();
      errorData.categories.forEach(category => {
        category.errors.forEach(errorGroup => {
          const { sequenceErrors } = processSequenceGroups(errorGroup);
          sequenceErrors.forEach((value: any, key: string) => {
            allSequenceErrors.set(key, value);
          });
        });
      });
      setSequenceSummaryItems(createSequenceSummary(allSequenceErrors));
    }
  }, [errorData]);

  const handleSaveCorrections = async () => {
    if (!projectId) return;
    try {
      setLoadingMessage('Saving corrections...');
      await validationService.saveCorrections(projectId, Array.from(corrections.values()));
      // Refresh error data
      await fetchErrors(projectId);
    } catch (error) {
      alert('Failed to save corrections: ' + (error as Error).message);
    }
  };

  const handleIgnoreErrors = async () => {
    if (!projectId) return;
    if (!confirm('Are you sure you want to ignore all remaining errors?')) return;
    try {
      setLoadingMessage('Ignoring errors...');
      await validationService.ignoreErrors(projectId);
      // Navigate to monitoring plan review after ignoring errors
      navigate(`/projects/${projectId}/monitoring-plan-review`);
    } catch (error) {
      alert('Failed to ignore errors: ' + (error as Error).message);
    }
  };

  const handleOpenChat = async () => {
    if (!projectId) return;
    try {
      setLoadingMessage('Initializing AI chat...');
      await validationService.initializeChatSession(projectId);
      navigate(`/projects/${projectId}/chat`);
    } catch (error) {
      alert('Failed to initialize chat: ' + (error as Error).message);
    }
  };

  const handleStartOver = () => {
    if (!confirm('Are you sure you want to start over? All progress will be lost.')) return;
    navigate(`/projects/${projectId}/upload`);
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
      setLoadingMessage('Generating CORSIA report...');
      await validationService.generateReport(projectId);
    } catch (error) {
      alert('Failed to generate report: ' + (error as Error).message);
    }
  };

  const handleRevalidate = async () => {
    if (!projectId) return;
    try {
      setLoadingMessage('Re-validating data...');
      await validationService.revalidate(projectId);
      // Refresh error data
      await fetchErrors(projectId);
    } catch (error) {
      alert('Failed to re-validate: ' + (error as Error).message);
    }
  };

  // Get column order from actual row data or fall back to fuel method
  const columnOrder = React.useMemo(() => {
    // Try to get column order from fuel method first
    if (selectedFuelMethod && FUEL_METHOD_COLUMNS[selectedFuelMethod]) {
      return FUEL_METHOD_COLUMNS[selectedFuelMethod];
    }

    // Fall back to extracting from first row in rows_data
    if (errorData && errorData.rows_data) {
      const rowKeys = Object.keys(errorData.rows_data);
      if (rowKeys.length > 0) {
        const firstRow = errorData.rows_data[parseInt(rowKeys[0])];
        if (firstRow && typeof firstRow === 'object') {
          const columns = Object.keys(firstRow).filter(key => key !== 'error' && key !== 'index');
          return columns;
        }
      }
    }

    // Default fallback
    return FUEL_METHOD_COLUMNS["Block Off - Block On"] || [];
  }, [selectedFuelMethod, errorData]);

  if (isLoading) {
    return <LoadingSection message={loadingMessage} />;
  }

  if (!errorData) {
    return <LoadingSection message="No validation data available" />;
  }

  // Check if there are errors
  const hasErrors = errorData.summary && errorData.summary.total_errors > 0;

  return (
    <div className="project-error-display">
      <ProjectHeader />
      <div className="container">
        <header>
          <h1>CSV Validation Results</h1>
          <p>Review and correct validation errors or proceed with clean data</p>
        </header>

        {hasErrors ? (
          // Error Display Section
          <div className="error-section">
            <h2>Validation Errors</h2>

            <ErrorSummary errorData={errorData} />

            <ActionButtons
              projectId={projectId || ''}
              onSaveCorrections={handleSaveCorrections}
              onIgnoreErrors={handleIgnoreErrors}
              onDownloadClean={handleDownloadClean}
              onDownloadErrors={handleDownloadErrors}
              onOpenChat={handleOpenChat}
              onStartOver={handleStartOver}
              hasCorrections={corrections.size > 0}
            />

            {/* Error Categories */}
            <div className="error-categories-container">
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

            {/* Final Sequence Error Summary */}
            {sequenceSummaryItems.length > 0 && (
              <div className="final-sequence-summary">
                <h4>Sequence Error Summary</h4>
                {sequenceSummaryItems.map((item) => (
                  <div key={item.key} className="sequence-summary-item">
                    <strong>Error:</strong> {item.errorCode}: Sequence Failed for Destination ICAO: {item.destinationICAO} to Origin ICAO: {item.originICAO}
                    <br />
                    <strong>Details:</strong> {item.errorCode} : {item.destinationICAO} → {item.originICAO}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          // Success Section
          <SuccessSection
            onGenerateReport={handleGenerateReport}
            onDownloadClean={handleDownloadClean}
            onRevalidate={handleRevalidate}
          />
        )}
      </div>

      <style jsx>{`
        .project-error-display {
          min-height: 100vh;
          background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
          background-attachment: fixed;
        }

        .container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 20px;
        }

        header {
          background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
          color: white;
          padding: 40px 30px;
          border-radius: 16px;
          margin-bottom: 30px;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
          text-align: center;
        }

        header h1 {
          margin: 0;
          font-size: 2rem;
          font-weight: 700;
          letter-spacing: -0.5px;
        }

        header p {
          margin: 0.5rem 0 0 0;
          opacity: 0.9;
          font-size: 1rem;
        }

        .error-section {
          background: white;
          border-radius: 1rem;
          padding: 2rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .error-section h2 {
          margin: 0 0 1.5rem 0;
          font-size: 1.5rem;
          font-weight: 700;
          color: #1f2937;
        }

        .error-categories-container {
          margin-top: 2rem;
        }

        .final-sequence-summary {
          margin-top: 2rem;
          padding: 1.5rem;
          background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
          border: 2px solid #fbbf24;
          border-radius: 0.75rem;
        }

        .final-sequence-summary h4 {
          margin: 0 0 1rem 0;
          font-size: 1.125rem;
          font-weight: 700;
          color: #92400e;
        }

        .sequence-summary-item {
          background: white;
          padding: 1rem;
          border-radius: 0.5rem;
          margin-bottom: 0.75rem;
          font-size: 0.875rem;
          color: #1f2937;
          line-height: 1.6;
        }

        .sequence-summary-item:last-child {
          margin-bottom: 0;
        }

        .sequence-summary-item strong {
          color: #991b1b;
        }
      `}</style>
    </div>
  );
};

export default ProjectValidation;
