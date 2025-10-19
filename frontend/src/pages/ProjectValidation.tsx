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
      setLoadingMessage('Saving corrections and reprocessing data...');
      // Save corrections - backend automatically reprocesses via validate_and_process_file
      await validationService.saveCorrections(projectId, Array.from(corrections.values()));

      setLoadingMessage('Refreshing validation results...');
      // Refresh error data to get updated results
      await fetchErrors(projectId);

      // Show success message
      alert('Corrections saved and data reprocessed successfully!');
    } catch (error) {
      console.error('Failed to save corrections:', error);
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
      setLoadingMessage('Opening AI chat...');
      // Simply navigate to chat - it will auto-initialize from projectId
      navigate(`/projects/${projectId}/chat`);
    } catch (error) {
      alert('Failed to open chat: ' + (error as Error).message);
    }
  };

  const handleStartOver = () => {
    if (!confirm('Are you sure you want to start over? All progress will be lost.')) return;
    navigate('/dashboard');
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
    <div className="min-h-screen bg-gradient-radial">
      <ProjectHeader />
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {hasErrors ? (
          // Error Display Section
          <>
            {/* Error Summary */}
            <div className="animate-fade-in mb-6">
              <ErrorSummary errorData={errorData} />
            </div>

            {/* Action Buttons */}
            <div className="bg-card rounded-xl p-6 shadow-card mb-6 animate-scale-in">
              <h3 className="font-semibold text-foreground/90 mb-4">Quick Actions</h3>
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
            </div>

            {/* Error Categories */}
            <div className="space-y-4">
              {errorData.categories.map((category, index) => (
                <div
                  key={`${category.name}-${index}`}
                  className="animate-fade-in-up"
                  style={{ animationDelay: `${index * 0.1}s`, animationFillMode: 'both' }}
                >
                  <ErrorCategory
                    category={category}
                    columnOrder={columnOrder}
                    rowsData={errorData.rows_data}
                    onCorrection={addCorrection}
                  />
                </div>
              ))}
            </div>

            {/* Final Sequence Error Summary */}
            {sequenceSummaryItems.length > 0 && (
              <div className="mt-6 bg-card rounded-xl p-6 border-l-4 border-warning shadow-card animate-scale-in">
                <h4 className="text-lg font-semibold text-warning mb-4 flex items-center gap-2">
                  <span>⚠️</span> Sequence Error Summary
                </h4>
                <div className="space-y-3">
                  {sequenceSummaryItems.map((item) => (
                    <div key={item.key} className="bg-muted/30 p-4 rounded-lg">
                      <div className="text-sm text-foreground/90">
                        <strong className="text-error">Error:</strong> {item.errorCode}: Sequence Failed for Destination ICAO: {item.destinationICAO} to Origin ICAO: {item.originICAO}
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        <strong>Details:</strong> {item.errorCode} : {item.destinationICAO} → {item.originICAO}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          // Success Section with Decorative Elements
          <div className="relative">
            {/* Decorative background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute top-10 left-10 w-72 h-72 bg-success/10 rounded-full blur-3xl animate-glow" />
              <div className="absolute bottom-10 right-10 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
            </div>
            <div className="relative">
              <SuccessSection
                onGenerateReport={handleGenerateReport}
                onDownloadClean={handleDownloadClean}
                onRevalidate={handleRevalidate}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectValidation;
