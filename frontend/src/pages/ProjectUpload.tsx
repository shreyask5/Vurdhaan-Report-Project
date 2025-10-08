/**
 * ProjectUpload Page
 * Handles CSV upload, column mapping, and validation workflow
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle, FileUp, Map, Settings, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { FileUploadSection } from '@/components/project/FileUploadSection';
import { ColumnMappingWizard } from '@/components/project/ColumnMappingWizard';
import { ValidationForm, type ValidationFormData } from '@/components/project/ValidationForm';
import { ErrorDisplay } from '@/components/project/ErrorDisplay';
import { validationService } from '@/services/validation';
import { projectsApi } from '@/services/api';
import type { ColumnMapping, ValidationResult } from '@/types/validation';

type Step = 'upload' | 'mapping' | 'configure' | 'results';

export default function ProjectUpload() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [projectName, setProjectName] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [csvColumns, setCsvColumns] = useState<string[]>([]);
  const [columnMapping, setColumnMapping] = useState<ColumnMapping>({});
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);

  useEffect(() => {
    if (projectId) {
      loadProject();
    }
  }, [projectId]);

  const loadProject = async () => {
    try {
      const project = await projectsApi.get(projectId!);
      setProjectName(project.name);
    } catch (error: any) {
      toast.error('Failed to load project');
      navigate('/dashboard');
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!projectId) return;

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const result = await validationService.uploadFile(
        projectId,
        file,
        (progress) => setUploadProgress(progress)
      );

      setCsvColumns(result.columns);
      const suggestedMapping = validationService.getSuggestedMapping(result.columns);
      setColumnMapping(suggestedMapping);

      toast.success('File uploaded successfully');
      setCurrentStep('mapping');
    } catch (error: any) {
      toast.error(error.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleMappingComplete = (mapping: ColumnMapping) => {
    setColumnMapping(mapping);
    setCurrentStep('configure');
    toast.success('Column mapping completed');
  };

  const handleValidate = async (formData: ValidationFormData) => {
    if (!projectId) return;

    setIsValidating(true);

    try {
      const result = await validationService.validateFile(projectId, {
        ...formData,
        column_mapping: columnMapping,
      });

      setValidationResult(result);
      setCurrentStep('results');

      if (result.is_valid) {
        toast.success('Validation completed successfully!');
      } else {
        toast.warning('Validation completed with errors');
      }
    } catch (error: any) {
      toast.error(error.message || 'Validation failed');
    } finally {
      setIsValidating(false);
    }
  };

  const handleDownloadClean = async () => {
    if (!projectId) return;

    try {
      const blob = await validationService.downloadCSV(projectId, 'clean');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'clean_data.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Downloaded clean data');
    } catch (error: any) {
      toast.error('Download failed');
    }
  };

  const handleDownloadErrors = async () => {
    if (!projectId) return;

    try {
      const blob = await validationService.downloadCSV(projectId, 'errors');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'errors_data.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Downloaded error data');
    } catch (error: any) {
      toast.error('Download failed');
    }
  };

  const handleSaveCorrections = async (corrections: { [rowIdx: number]: any }) => {
    if (!projectId) return;

    try {
      await validationService.saveCorrections(projectId, corrections);
      toast.success('Corrections saved successfully');
    } catch (error: any) {
      toast.error('Failed to save corrections');
    }
  };

  const handleGenerateReport = async () => {
    if (!projectId) return;

    try {
      const blob = await validationService.generateReport(projectId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `corsia_report_${projectId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('CORSIA report generated');
    } catch (error: any) {
      toast.error('Report generation failed');
    }
  };

  const steps = [
    { key: 'upload', label: 'Upload File', icon: FileUp },
    { key: 'mapping', label: 'Map Columns', icon: Map },
    { key: 'configure', label: 'Configure', icon: Settings },
    { key: 'results', label: 'Results', icon: CheckCircle },
  ];

  const currentStepIndex = steps.findIndex((s) => s.key === currentStep);
  const progressPercentage = ((currentStepIndex + 1) / steps.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/dashboard">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Dashboard
                </Link>
              </Button>
              <div className="h-8 w-px bg-border" />
              <div>
                <h1 className="text-lg font-semibold">{projectName || 'Project'}</h1>
                <p className="text-xs text-muted-foreground">CSV Upload & Validation</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-card border-b border-border">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="mb-4">
            <Progress value={progressPercentage} className="h-2" />
          </div>
          <div className="grid grid-cols-4 gap-4">
            {steps.map((step, idx) => {
              const Icon = step.icon;
              const isActive = step.key === currentStep;
              const isCompleted = idx < currentStepIndex;

              return (
                <div
                  key={step.key}
                  className={`flex items-center gap-2 ${
                    isActive ? 'text-primary' : isCompleted ? 'text-success' : 'text-muted-foreground'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : isCompleted
                        ? 'bg-success text-success-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    {isCompleted ? <CheckCircle className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  </div>
                  <span className="text-sm font-medium hidden sm:inline">{step.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-4xl mx-auto">
          {currentStep === 'upload' && (
            <FileUploadSection
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
            />
          )}

          {currentStep === 'mapping' && (
            <ColumnMappingWizard
              csvColumns={csvColumns}
              suggestedMapping={columnMapping}
              onMappingComplete={handleMappingComplete}
            />
          )}

          {currentStep === 'configure' && (
            <ValidationForm onValidate={handleValidate} isValidating={isValidating} />
          )}

          {currentStep === 'results' && validationResult && (
            <div className="space-y-6">
              {validationResult.is_valid ? (
                <div className="bg-success/10 border border-success/20 rounded-lg p-6 text-center">
                  <CheckCircle className="h-12 w-12 text-success mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-success mb-2">Validation Successful!</h2>
                  <p className="text-muted-foreground">
                    Your flight data has been validated successfully with no errors.
                  </p>
                  <div className="flex gap-4 justify-center mt-6">
                    <Button onClick={handleDownloadClean}>Download Clean Data</Button>
                    <Button onClick={handleGenerateReport} variant="outline">
                      Generate CORSIA Report
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  {validationResult.error_data && (
                    <ErrorDisplay
                      errorData={validationResult.error_data}
                      onSaveCorrections={handleSaveCorrections}
                      onDownloadClean={handleDownloadClean}
                      onDownloadErrors={handleDownloadErrors}
                    />
                  )}
                  <div className="flex gap-4">
                    <Button onClick={handleGenerateReport} className="flex-1">
                      Generate CORSIA Report
                    </Button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
