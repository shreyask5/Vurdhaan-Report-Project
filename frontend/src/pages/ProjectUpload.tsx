import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useValidation } from '../contexts/ValidationContext';
import { SchemeSelector } from '../components/project/SchemeSelector';
import { MonitoringPlanUpload } from '../components/project/MonitoringPlanUpload';
import { FileUploadSection } from '../components/project/FileUploadSection';
import { FuelMethodSelector } from '../components/project/FuelMethodSelector';
import { ColumnMappingWizard } from '../components/project/ColumnMappingWizard';
import { ValidationForm } from '../components/project/ValidationForm';
import { ValidationParams, SchemeType, AirlineSize } from '../types/validation';
import { projectsApi } from '../services/api';

const ProjectUpload: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [uploadStatus, setUploadStatus] = useState<any>(null);
  const [isCheckingStatus, setIsCheckingStatus] = useState(true);
  const {
    currentStep,
    selectedScheme,
    airlineSize,
    monitoringPlanData,
    selectedFile,
    selectedFuelMethod,
    uploadedColumns,
    columnMapping,
    isLoading,
    setScheme,
    uploadMonitoringPlan,
    setFile,
    setFuelMethod,
    setColumnMapping,
    uploadFile,
    goToStep
  } = useValidation();

  // Check upload status on mount
  useEffect(() => {
    const checkStatus = async () => {
      console.log('[PROJECT UPLOAD DEBUG] Checking upload status for project:', projectId);
      if (!projectId) return;

      try {
        const status = await projectsApi.getUploadStatus(projectId);
        console.log('[PROJECT UPLOAD DEBUG] Upload status received:', status);
        setUploadStatus(status);

        // If already uploaded and validated, redirect to error display
        if (status.upload_completed && status.validation_status !== null) {
          console.log('[PROJECT UPLOAD DEBUG] File already uploaded, redirecting to errors page');
          navigate(`/projects/${projectId}/errors`, { replace: true });
        } else {
          console.log('[PROJECT UPLOAD DEBUG] Upload page allowed - upload_completed:', status.upload_completed);
        }
      } catch (error) {
        console.error('[PROJECT UPLOAD ERROR] Failed to check upload status:', error);
      } finally {
        setIsCheckingStatus(false);
      }
    };

    checkStatus();
  }, [projectId, navigate]);

  const handleSchemeSelect = async (scheme: SchemeType, airlineSize: AirlineSize) => {
    if (!projectId) return;
    await setScheme(projectId, scheme, airlineSize);
  };

  const handleMonitoringPlanUpload = async (file: File) => {
    if (!projectId) return;
    await uploadMonitoringPlan(projectId, file);
  };

  const handleValidationSubmit = async (params: ValidationParams) => {
    if (!selectedFuelMethod || !projectId) return;

    const fullParams = {
      ...params,
      column_mapping: columnMapping,
      fuel_method: selectedFuelMethod
    };

    try {
      await uploadFile(projectId, fullParams);
      // Navigate to validation page after upload
      navigate(`/projects/${projectId}/validation`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    }
  };

  // Auto-select fuel method from project metadata when entering Parameters
  useEffect(() => {
    const fetchProjectDefaults = async () => {
      if (!projectId || currentStep !== 'parameters') return;
      try {
        const p = await projectsApi.get(projectId);
        const fm = p?.file_metadata?.fuel_method;
        if (fm) setFuelMethod(fm as any);
      } catch (e) {
        console.warn('Could not auto-select fuel method:', e);
      }
    };
    fetchProjectDefaults();
  }, [projectId, currentStep, setFuelMethod]);

  // Editable monitoring plan (parameters) state and save with debounce
  const [editablePlan, setEditablePlan] = useState<any | null>(null);
  const saveTimer = useRef<number | null>(null);
  useEffect(() => {
    if (currentStep === 'parameters') {
      setEditablePlan(monitoringPlanData || null);
    }
  }, [currentStep, monitoringPlanData]);

  const saveMonitoringPlan = useMemo(() => {
    return async (plan: any) => {
      if (!projectId) return;
      try {
        await fetch(`/api/projects/${projectId}/monitoring-plan`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(plan)
        });
      } catch (e) {
        console.error('Failed saving monitoring plan edits', e);
      }
    };
  }, [projectId]);

  const onEditPlanField = (path: string[], value: any) => {
    setEditablePlan((prev: any) => {
      const next = { ...(prev || {}) } as any;
      let cursor: any = next;
      for (let i = 0; i < path.length - 1; i++) {
        const key = path[i];
        cursor[key] = cursor[key] ?? {};
        cursor = cursor[key];
      }
      cursor[path[path.length - 1]] = value;
      if (saveTimer.current) window.clearTimeout(saveTimer.current);
      saveTimer.current = window.setTimeout(() => saveMonitoringPlan(next), 600);
      return next;
    });
  };

  // Show loading while checking status
  if (isCheckingStatus) {
    return (
      <div className="min-h-screen bg-gradient-radial flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 shadow-xl text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-4"></div>
          <p className="text-lg font-semibold text-gray-700">Checking project status...</p>
        </div>
      </div>
    );
  }

  // Show message if already uploaded
  if (uploadStatus?.upload_completed) {
    return (
      <div className="min-h-screen bg-gradient-radial flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 shadow-xl text-center max-w-md">
          <div className="text-yellow-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">File Already Uploaded</h2>
          <p className="text-gray-600 mb-4">
            This project already has a file uploaded. Create a new project to upload a different file.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-primary-dark transition"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-radial">
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-primary hover:text-primary-dark mb-4 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-800">CSV Upload & Validation</h1>
          <p className="text-gray-600 mt-2">
            Upload your flight data CSV file and validate it against CORSIA requirements
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8 bg-white rounded-xl p-6 shadow-card">
          <div className="flex items-center justify-between">
            {['Scheme', 'Monitoring Plan', 'Parameters', 'Upload', 'Column Mapping'].map((step, index) => {
              const stepKeys = ['scheme', 'monitoring_plan', 'parameters', 'upload', 'mapping'];
              const currentIndex = stepKeys.indexOf(currentStep);
              const isActive = index === currentIndex;
              const isCompleted = index < currentIndex;

              return (
                <React.Fragment key={step}>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold text-sm transition-all ${
                        isActive
                          ? 'bg-primary text-white'
                          : isCompleted
                          ? 'bg-success text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      {isCompleted ? '✓' : index + 1}
                    </div>
                    <span
                      className={`text-sm font-medium ${
                        isActive ? 'text-primary' : isCompleted ? 'text-success' : 'text-gray-500'
                      }`}
                    >
                      {step}
                    </span>
                  </div>
                  {index < 4 && (
                    <div
                      className={`flex-1 h-1 mx-4 rounded ${
                        isCompleted ? 'bg-success' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="step-content">
          {currentStep === 'scheme' && (
            <div className="bg-white rounded-2xl p-8 shadow-card">
              <SchemeSelector
                onSelect={handleSchemeSelect}
                selectedScheme={selectedScheme}
                selectedAirlineSize={airlineSize}
              />
            </div>
          )}

          {currentStep === 'monitoring_plan' && (
            <div className="bg-white rounded-2xl p-8 shadow-card">
              <MonitoringPlanUpload
                onUpload={handleMonitoringPlanUpload}
                extractedData={monitoringPlanData}
                onBack={() => goToStep('scheme')}
              />
            </div>
          )}

          {currentStep === 'parameters' && (
            <div className="bg-white rounded-2xl p-8 shadow-card">
              <h2 className="text-2xl font-semibold mb-6 text-gray-700">Parameters</h2>
              {/* Fuel Method inside Parameters */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold mb-3 text-gray-700">Fuel Calculation Method</h3>
                <FuelMethodSelector onSelect={setFuelMethod} selectedMethod={selectedFuelMethod} />
              </div>

              {/* Editable Monitoring Plan (basic fields) */}
              {editablePlan && (
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-gray-700">Extracted Monitoring Plan</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-600">Operator Name</label>
                      <input
                        className="mt-1 w-full border rounded px-3 py-2"
                        value={editablePlan?.operator?.name?.value || ''}
                        onChange={(e) => onEditPlanField(['operator','name','value'], e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">ICAO Designator</label>
                      <input
                        className="mt-1 w-full border rounded px-3 py-2"
                        value={editablePlan?.flight_attribution?.icao_designator || ''}
                        onChange={(e) => onEditPlanField(['flight_attribution','icao_designator'], e.target.value)}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">Activities Description</label>
                    <textarea
                      className="mt-1 w-full border rounded px-3 py-2"
                      rows={4}
                      value={editablePlan?.activities?.description || ''}
                      onChange={(e) => onEditPlanField(['activities','description'], e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {currentStep === 'upload' && (
            <div className="bg-white rounded-2xl p-8 shadow-card">
              <h2 className="text-2xl font-semibold mb-6 text-gray-700">Upload CSV File</h2>
              <FileUploadSection onFileSelect={setFile} />
            </div>
          )}

          {/* Fuel method step removed; now handled within Parameters */}

          {currentStep === 'mapping' && selectedFuelMethod && (
            <ColumnMappingWizard
              uploadedColumns={uploadedColumns}
              fuelMethod={selectedFuelMethod}
              onComplete={setColumnMapping}
              onBack={() => goToStep('fuel_method')}
            />
          )}

          {currentStep === 'parameters' && (
            <ValidationForm
              onSubmit={handleValidationSubmit}
              onBack={() => goToStep('mapping')}
            />
          )}
        </div>

        {/* Loading Overlay */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 shadow-xl text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-4"></div>
              <p className="text-lg font-semibold text-gray-700">Processing your file...</p>
              <p className="text-sm text-gray-500 mt-2">This may take a moment</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectUpload;
