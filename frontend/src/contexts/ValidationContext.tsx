import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ErrorData, Correction, ValidationFormData, ColumnMapping, FuelMethod } from '../types/validation';
import { validationService } from '../services/validation';
import { readCSVColumns } from '../utils/csv';

type ValidationStep = 'upload' | 'fuel_method' | 'mapping' | 'parameters' | 'validation' | 'success';

interface ValidationContextType {
  // State
  fileId: string | null;
  errorData: ErrorData | null;
  corrections: Map<string, Correction>;
  isLoading: boolean;
  currentStep: ValidationStep;

  // File/Fuel Method
  selectedFile: File | null;
  selectedFuelMethod: FuelMethod | null;
  uploadedColumns: string[];
  columnMapping: ColumnMapping;

  // Actions
  setFile: (file: File) => Promise<void>;
  setFuelMethod: (method: FuelMethod) => void;
  setColumnMapping: (mapping: ColumnMapping) => void;
  uploadFile: (projectId: string, params: ValidationFormData) => Promise<void>;
  fetchErrors: () => Promise<void>;
  saveCorrections: () => Promise<void>;
  ignoreErrors: () => Promise<void>;
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
  const [currentStep, setCurrentStep] = useState<ValidationStep>('upload');

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFuelMethod, setSelectedFuelMethod] = useState<FuelMethod | null>(null);
  const [uploadedColumns, setUploadedColumns] = useState<string[]>([]);
  const [columnMapping, setColumnMappingState] = useState<ColumnMapping>({});

  const setFile = async (file: File) => {
    setSelectedFile(file);
    const columns = await readCSVColumns(file);
    setUploadedColumns(columns);
    setCurrentStep('fuel_method');
  };

  const setFuelMethod = (method: FuelMethod) => {
    setSelectedFuelMethod(method);
    setCurrentStep('mapping');
  };

  const setColumnMapping = (mapping: ColumnMapping) => {
    setColumnMappingState(mapping);
    setCurrentStep('parameters');
  };

  const uploadFile = async (projectId: string, params: ValidationFormData) => {
    if (!selectedFile) throw new Error('No file selected');

    setIsLoading(true);
    try {
      const response = await validationService.uploadFile(projectId, selectedFile, params);
      setFileId(response.file_id);

      if (response.errors) {
        setErrorData(response.errors);
        setCurrentStep('validation');
      } else if (response.success) {
        setCurrentStep('success');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchErrors = async () => {
    if (!fileId) return;

    setIsLoading(true);
    try {
      const errors = await validationService.fetchErrors(fileId);
      setErrorData(errors);
    } finally {
      setIsLoading(false);
    }
  };

  const saveCorrections = async () => {
    if (!fileId) return;

    setIsLoading(true);
    try {
      await validationService.saveCorrections(fileId, Array.from(corrections.values()));
      setCorrections(new Map());
      await fetchErrors();
    } finally {
      setIsLoading(false);
    }
  };

  const ignoreErrors = async () => {
    if (!fileId) return;

    setIsLoading(true);
    try {
      await validationService.ignoreErrors(fileId);
      setCurrentStep('success');
    } finally {
      setIsLoading(false);
    }
  };

  const addCorrection = (correction: Correction) => {
    const key = `${correction.row_idx}_${correction.column}`;
    setCorrections(prev => new Map(prev).set(key, correction));
  };

  const reset = () => {
    setFileId(null);
    setErrorData(null);
    setCorrections(new Map());
    setSelectedFile(null);
    setSelectedFuelMethod(null);
    setUploadedColumns([]);
    setColumnMappingState({});
    setCurrentStep('upload');
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
      selectedFile,
      selectedFuelMethod,
      uploadedColumns,
      columnMapping,
      setFile,
      setFuelMethod,
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
