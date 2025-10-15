import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useValidation } from '../contexts/ValidationContext';
import { SchemeSelector } from '../components/project/SchemeSelector';
import { MonitoringPlanUpload } from '../components/project/MonitoringPlanUpload';
import { MonitoringPlanEditor } from '../components/project/MonitoringPlanEditor';
import { FileUploadSection } from '../components/project/FileUploadSection';
import { FuelMethodSelector } from '../components/project/FuelMethodSelector';
import { ColumnMappingWizard } from '../components/project/ColumnMappingWizard';
import { ValidationForm } from '../components/project/ValidationForm';
import { ValidationParams, SchemeType, AirlineSize, FuelMethod } from '../types/validation';
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














  // TEMP: For testing, skip the Monitoring Plan step entirely
  // NOTE: Remove this effect to re-enable the Monitoring Plan step
  useEffect(() => {
    if (currentStep === 'monitoring_plan') {
      goToStep('parameters');
    }
  }, [currentStep, goToStep]);

  // REMOVE THIS SECTION AFTER TESTING















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
      if (selectedFuelMethod) return; // Already set

      try {
        const p = await projectsApi.get(projectId);
        const fm = p?.file_metadata?.fuel_method;
        if (fm && !selectedFuelMethod) {
          setFuelMethod(fm as FuelMethod);
        }
      } catch (e) {
        console.warn('Could not auto-select fuel method:', e);
      }
    };
    fetchProjectDefaults();
  }, [projectId, currentStep, selectedFuelMethod, setFuelMethod]);

  // Editable monitoring plan (parameters) state and save with debounce
  const [editablePlan, setEditablePlan] = useState<any | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const saveTimer = useRef<number | null>(null);

  useEffect(() => {
    if (currentStep === 'parameters' && monitoringPlanData) {
      setEditablePlan(monitoringPlanData);
    }
  }, [currentStep, monitoringPlanData]);

  const saveMonitoringPlan = useMemo(() => {
    return async (plan: any) => {
      if (!projectId) return;
      setSaveStatus('saving');
      try {
        await projectsApi.updateMonitoringPlan(projectId, plan);
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } catch (e) {
        console.error('Failed saving monitoring plan edits', e);
        setSaveStatus('idle');
      }
    };
  }, [projectId]);

  const onEditPlanField = (path: string[], value: any) => {
    setEditablePlan((prev: any) => {
      const next = JSON.parse(JSON.stringify(prev || {})); // Deep clone
      let cursor: any = next;
      for (let i = 0; i < path.length - 1; i++) {
        const key = path[i];
        if (!cursor[key]) cursor[key] = {};
        cursor = cursor[key];
      }
      cursor[path[path.length - 1]] = value;

      // Debounced save
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
            {['Scheme', 'Monitoring Plan', 'Parameters', 'Flight Data', 'Column Mapping'].map((step, index) => {
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














          {/* TEMP: Monitoring Plan upload is disabled for testing. */}
          {currentStep === 'monitoring_plan' && (
            // TEMP: Monitoring Plan upload is disabled for testing.
            // To re-enable, uncomment the block below.
            // <div className="bg-white rounded-2xl p-8 shadow-card">
            //   <MonitoringPlanUpload
            //     projectId={projectId!}
            //     onUpload={handleMonitoringPlanUpload}
            //     extractedData={monitoringPlanData}
            //     onBack={() => goToStep('scheme')}
            //     onComplete={() => goToStep('parameters')}
            //   />
            // </div>
            null
          )}














          {currentStep === 'parameters' && (
            <div className="bg-white rounded-2xl p-8 shadow-card space-y-8">
              <div>
                <h2 className="text-2xl font-semibold text-gray-700 mb-2">Parameters</h2>
                <p className="text-gray-600">
                  Review and configure your project parameters and monitoring plan details.
                </p>
              </div>

              {/* Save Status Indicator */}
              {saveStatus !== 'idle' && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center gap-2">
                  {saveStatus === 'saving' && (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm text-blue-700">Saving changes...</span>
                    </>
                  )}
                  {saveStatus === 'saved' && (
                    <>
                      <span className="text-green-600">✓</span>
                      <span className="text-sm text-green-700">Changes saved</span>
                    </>
                  )}
                </div>
              )}

              {/* Fuel Method Selector */}
              <div className="border-b border-gray-200 pb-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-700">Fuel Calculation Method</h3>
                <FuelMethodSelector onSelect={setFuelMethod} selectedMethod={selectedFuelMethod} />
              </div>

              {/* Monitoring Plan Editor */}
              {editablePlan && (
                <div>
                  <h3 className="text-lg font-semibold mb-4 text-gray-700">Monitoring Plan Details</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Review and edit the extracted monitoring plan information. All changes are automatically saved.
                  </p>
                  <MonitoringPlanEditor data={editablePlan} onEdit={onEditPlanField} />
                </div>
              )}

              {!editablePlan && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800">
                    ⚠️ No monitoring plan data available. Please upload a monitoring plan in the previous step.
                  </p>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between pt-6 border-t border-gray-200">
                <button
                  // TEMP: Monitoring Plan step skipped for testing; go back to Scheme instead
                  onClick={() => goToStep('scheme')}
                  className="px-6 py-2 border-2 border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                >
                  ← Back to Monitoring Plan
                </button>
                <button
                  onClick={() => goToStep('upload')}
                  disabled={!selectedFuelMethod}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    selectedFuelMethod
                      ? 'bg-primary text-white hover:bg-primary-dark'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  Continue to Flight Data →
                </button>
              </div>
            </div>
          )}

          {currentStep === 'upload' && (
            <div className="bg-white rounded-2xl p-8 shadow-card space-y-6">
              <div>
                <h2 className="text-2xl font-semibold text-gray-700 mb-2">Upload Flight Data</h2>
                <p className="text-gray-600">
                  Upload your flight data CSV file for validation.
                </p>
              </div>
              <FileUploadSection onFileSelect={setFile} />
              <div className="flex justify-between pt-4 border-t border-gray-200">
                <button
                  onClick={() => goToStep('parameters')}
                  className="px-6 py-2 border-2 border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                >
                  ← Back to Parameters
                </button>
              </div>
            </div>
          )}

          {currentStep === 'mapping' && selectedFuelMethod && (
            <ColumnMappingWizard
              uploadedColumns={uploadedColumns}
              fuelMethod={selectedFuelMethod}
              onComplete={setColumnMapping}
              onBack={() => goToStep('upload')}
            />
          )}

          {currentStep === 'validation' && (
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
