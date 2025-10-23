import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useValidation } from '../contexts/ValidationContext';
import { ErrorSummary } from '../components/project/ErrorSummary';
import { ErrorCategory } from '../components/project/ErrorCategory';
import { ActionButtons } from '../components/project/ActionButtons';
import { SuccessSection } from '../components/project/SuccessSection';
import { LoadingSection } from '../components/project/LoadingSection';
import { FUEL_METHOD_COLUMNS, ErrorMetadata } from '../types/validation';
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
  const [aiChatEnabled, setAiChatEnabled] = useState(false);
  const hasFetchedRef = React.useRef(false);

  // Pagination state
  const [usePagination, setUsePagination] = useState(false);
  const [errorMetadata, setErrorMetadata] = useState<ErrorMetadata | null>(null);
  const [metadataError, setMetadataError] = useState<string | null>(null);

  // Fetch project details to get ai_chat_enabled
  React.useEffect(() => {
    if (projectId) {
      import('../services/api').then(({ projectsApi }) => {
        projectsApi.get(projectId)
          .then(project => {
            setAiChatEnabled(project.ai_chat_enabled || false);
          })
          .catch(error => {
            console.error('[PROJECT VALIDATION] Failed to fetch project details:', error);
          });
      });
    }
  }, [projectId]);

  // Fetch error metadata first to determine if pagination is available
  React.useEffect(() => {
    if (projectId && !hasFetchedRef.current) {
      hasFetchedRef.current = true;
      console.log('[PROJECT VALIDATION] Attempting to fetch error metadata for project:', projectId);

      // Fetch paginated metadata (pagination-only mode)
      validationService.fetchErrorMetadata(projectId)
        .then(metadata => {
          console.log('[PROJECT VALIDATION] Successfully fetched error metadata:', metadata);
          setErrorMetadata(metadata);
          setUsePagination(true);
          setLoadingMessage('Validation results loaded');
        })
        .catch(error => {
          console.log('[PROJECT VALIDATION] No error metadata available - validation passed with no errors');
          // If metadata doesn't exist, it means there are no errors (validation passed)
          setErrorMetadata({
            total_errors: 0,
            error_rows: 0,
            error_categories: 0,
            categories: []
          });
          setUsePagination(true); // Still use pagination mode (just with no errors)
          setLoadingMessage('Validation passed - no errors found');
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

  // Determine if we have errors (from either mode)
  const hasErrors = usePagination
    ? (errorMetadata && errorMetadata.total_errors > 0)
    : (errorData && errorData.summary && errorData.summary.total_errors > 0);

  // Show loading if we're still fetching in legacy mode
  if (!usePagination && !errorData) {
    return <LoadingSection message="No validation data available" />;
  }

  // Show loading if we're in pagination mode but metadata isn't loaded yet
  if (usePagination && !errorMetadata && !metadataError) {
    return <LoadingSection message="Loading error metadata..." />;
  }

  return (
    <div className="min-h-screen bg-gradient-radial">
      <ProjectHeader />
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {hasErrors ? (
          // Error Display Section
          <>
            {/* Error Summary */}
            <div className="animate-fade-in mb-6">
              {usePagination && errorMetadata ? (
                // Paginated mode summary
                <div className="bg-card rounded-xl p-6 shadow-card">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-error/10 rounded-lg p-4">
                      <div className="text-3xl font-bold text-error">{errorMetadata.total_errors}</div>
                      <div className="text-sm text-muted-foreground">Total Errors</div>
                    </div>
                    <div className="bg-warning/10 rounded-lg p-4">
                      <div className="text-3xl font-bold text-warning">{errorMetadata.error_rows}</div>
                      <div className="text-sm text-muted-foreground">Affected Rows</div>
                    </div>
                    <div className="bg-primary/10 rounded-lg p-4">
                      <div className="text-3xl font-bold text-primary">{errorMetadata.error_categories}</div>
                      <div className="text-sm text-muted-foreground">Error Categories</div>
                    </div>
                  </div>
                </div>
              ) : (
                // Legacy mode summary
                errorData && <ErrorSummary errorData={errorData} />
              )}
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
                aiChatEnabled={aiChatEnabled}
              />
            </div>

            {/* Error Categories */}
            <div className="space-y-4">
              {usePagination && errorMetadata ? (
                // Paginated mode - render categories from metadata
                errorMetadata.categories.map((categoryMeta, index) => (
                  <div
                    key={`${categoryMeta.name}-${index}`}
                    className="animate-fade-in-up"
                    style={{ animationDelay: `${index * 0.1}s`, animationFillMode: 'both' }}
                  >
                    <ErrorCategory
                      categoryMetadata={categoryMeta}
                      projectId={projectId}
                      columnOrder={columnOrder}
                      onCorrection={addCorrection}
                      usePagination={true}
                    />
                  </div>
                ))
              ) : (
                // Legacy mode - render categories from errorData
                errorData && errorData.categories.map((category, index) => (
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
                      usePagination={false}
                    />
                  </div>
                ))
              )}
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
