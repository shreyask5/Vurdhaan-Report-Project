import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import { ErrorData, Correction, ValidationFormData, ColumnMapping, FuelMethod, SchemeType, AirlineSize, MonitoringPlanData, DateFormat } from '../types/validation';
import { validationService } from '../services/validation';
import { readCSVColumns } from '../utils/csv';
import { projectsApi } from '../services/api';

type ValidationStep = 'scheme' | 'monitoring_plan' | 'parameters' | 'upload' | 'mapping' | 'validation' | 'success';

interface ValidationParams {
  monitoring_year: string;
  date_format: DateFormat;
  flight_starts_with: string;
}

interface ValidationContextType {
  // State
  fileId: string | null;
  errorData: ErrorData | null;
  corrections: Map<string, Correction>;
  isLoading: boolean;
  currentStep: ValidationStep;

  // Scheme & Monitoring Plan
  selectedScheme: SchemeType | null;
  airlineSize: AirlineSize | null;
  monitoringPlanData: MonitoringPlanData | null;

  // File/Fuel Method
  selectedFile: File | null;
  selectedFuelMethod: FuelMethod | null;
  uploadedColumns: string[];
  columnMapping: ColumnMapping;

  // Validation Parameters
  validationParams: ValidationParams | null;

  // Actions
  setScheme: (projectId: string, scheme: SchemeType) => Promise<void>;
  uploadMonitoringPlan: (projectId: string, file: File) => Promise<void>;
  setFile: (file: File) => Promise<void>;
  setFuelMethod: (method: FuelMethod) => void;
  setValidationParams: (params: ValidationParams) => void;
  setColumnMapping: (mapping: ColumnMapping) => void;
  uploadFile: (projectId: string, params: ValidationFormData) => Promise<void>;
  fetchErrors: (projectId?: string) => Promise<void>;
  saveCorrections: (projectId: string) => Promise<void>;
  ignoreErrors: (projectId: string) => Promise<void>;
  addCorrection: (correction: Correction) => void;
  reset: () => void;
  goToStep: (step: ValidationStep) => void;
}

export const ValidationContext = createContext<ValidationContextType | undefined>(undefined);

export const ValidationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [fileId, setFileId] = useState<string | null>(null);
  const [errorData, setErrorData] = useState<ErrorData | null>(null);
  const [corrections, setCorrections] = useState<Map<string, Correction>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<ValidationStep>('scheme');

  const [selectedScheme, setSelectedSchemeState] = useState<SchemeType | null>(null);
  const [airlineSize, setAirlineSizeState] = useState<AirlineSize | null>(null);
  const [monitoringPlanData, setMonitoringPlanData] = useState<MonitoringPlanData | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFuelMethod, setSelectedFuelMethod] = useState<FuelMethod | null>(null);
  const [uploadedColumns, setUploadedColumns] = useState<string[]>([]);
  const [columnMapping, setColumnMappingState] = useState<ColumnMapping>({});

  const currentYear = new Date().getFullYear();
  const [validationParams, setValidationParamsState] = useState<ValidationParams | null>({
    monitoring_year: currentYear.toString(),
    date_format: 'DMY',
    flight_starts_with: ''
  });

  const setScheme = async (projectId: string, scheme: SchemeType) => {
    setIsLoading(true);
    try {
      await projectsApi.updateScheme(projectId, scheme);
      setSelectedSchemeState(scheme);
      setCurrentStep('monitoring_plan');
    } finally {
      setIsLoading(false);
    }
  };

  const uploadMonitoringPlan = async (projectId: string, file: File) => {
    setIsLoading(true);
    try {
      // Upload file - extraction happens in background
      await projectsApi.uploadMonitoringPlan(projectId, file);
      // Don't wait for extraction, let it run async
      // User can proceed to parameters immediately
      setCurrentStep('parameters');
    } finally {
      setIsLoading(false);
    }
  };

  const setValidationParams = (params: ValidationParams) => {
    setValidationParamsState(params);
  };

  const setFile = async (file: File) => {
    setSelectedFile(file);
    const columns = await readCSVColumns(file);
    setUploadedColumns(columns);
    setCurrentStep('mapping');
  };

  const setFuelMethod = (method: FuelMethod) => {
    setSelectedFuelMethod(method);
  };

  const setColumnMapping = (mapping: ColumnMapping) => {
    setColumnMappingState(mapping);
    setCurrentStep('validation');
  };

  const uploadFile = async (projectId: string, params: ValidationFormData) => {
    if (!selectedFile) throw new Error('No file selected');

    setIsLoading(true);
    try {
      const response = await validationService.uploadFile(projectId, selectedFile, params);
      setFileId(response.file_id || projectId);

      // Fetch errors after upload
      const errors = await validationService.fetchErrors(projectId);
      setErrorData(errors);

      if (errors && errors.summary && errors.summary.total_errors > 0) {
        setCurrentStep('validation');
      } else {
        setCurrentStep('success');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchErrors = useCallback(async (projectId?: string) => {
    const id = projectId || fileId;
    if (!id) return;

    setIsLoading(true);
    try {
      const errors = await validationService.fetchErrors(id);
      setErrorData(errors);
    } finally {
      setIsLoading(false);
    }
  }, [fileId]);

  const saveCorrections = async (projectId: string) => {
    if (!projectId) return;

    setIsLoading(true);
    try {
      await validationService.saveCorrections(projectId, Array.from(corrections.values()));
      setCorrections(new Map());
      await fetchErrors(projectId);
    } finally {
      setIsLoading(false);
    }
  };

  const ignoreErrors = async (projectId: string) => {
    if (!projectId) return;

    setIsLoading(true);
    try {
      await validationService.ignoreErrors(projectId);
      setCurrentStep('success');
    } finally {
      setIsLoading(false);
    }
  };

  const addCorrection = useCallback((correction: Correction) => {
    const key = `${correction.row_idx}-${correction.column}`;
    setCorrections(prev => {
      const newMap = new Map(prev);
      // Remove correction if value reverted to original (matches index4.html behavior)
      if (correction.new_value === correction.old_value) {
        newMap.delete(key);
      } else {
        newMap.set(key, correction);
      }
      return newMap;
    });
  }, []);

  const reset = () => {
    setFileId(null);
    setErrorData(null);
    setCorrections(new Map());
    setSelectedSchemeState(null);
    setAirlineSizeState(null);
    setMonitoringPlanData(null);
    setSelectedFile(null);
    setSelectedFuelMethod(null);
    setUploadedColumns([]);
    setColumnMappingState({});
    setCurrentStep('scheme');
  };

  const goToStep = (step: ValidationStep) => {
    setCurrentStep(step);
  };

  return (
    <ValidationContext.Provider value={{
      fileId,
      errorData,
      corrections,
      isLoading,
      currentStep,
      selectedScheme,
      airlineSize,
      monitoringPlanData,
      selectedFile,
      selectedFuelMethod,
      uploadedColumns,
      columnMapping,
      validationParams,
      setScheme,
      uploadMonitoringPlan,
      setFile,
      setFuelMethod,
      setValidationParams,
      setColumnMapping,
      uploadFile,
      fetchErrors,
      saveCorrections,
      ignoreErrors,
      addCorrection,
      reset,
      goToStep
    }}>
      {children}
    </ValidationContext.Provider>
  );
};

export const useValidation = () => {
  const context = useContext(ValidationContext);
  if (!context) throw new Error('useValidation must be used within ValidationProvider');
  return context;
};
