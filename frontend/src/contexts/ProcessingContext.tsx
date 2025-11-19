/**
 * Context para manejar el estado de procesamiento de documentos
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { processingService } from '@/services';
import { HistoriaClinicaProcesada, HistoriaClinicaConsolidada } from '@/types';

/**
 * Estados de procesamiento
 */
export type ProcessingStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

/**
 * Metadata del empleado
 */
export interface EmpleadoMetadata {
  empresaId: string;
  empresaNombre: string;
  documento: string;
  gesId?: string;
  cargo?: string;
}

/**
 * Estado del contexto
 */
interface ProcessingState {
  // Estado
  status: ProcessingStatus;
  progress: number;
  currentFile: string | null;
  error: string | null;
  result: HistoriaClinicaProcesada | HistoriaClinicaConsolidada | null;

  // Acciones
  processDocument: (file: File) => Promise<void>;
  processPersonDocuments: (files: File[], metadata: EmpleadoMetadata) => Promise<void>;
  reset: () => void;
}

const ProcessingContext = createContext<ProcessingState | undefined>(undefined);

/**
 * Props del provider
 */
interface ProcessingProviderProps {
  children: ReactNode;
}

/**
 * Provider del contexto de procesamiento
 */
export const ProcessingProvider: React.FC<ProcessingProviderProps> = ({ children }) => {
  const [status, setStatus] = useState<ProcessingStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HistoriaClinicaProcesada | HistoriaClinicaConsolidada | null>(
    null
  );

  /**
   * Procesar un solo documento
   */
  const processDocument = useCallback(async (file: File) => {
    try {
      setStatus('uploading');
      setProgress(0);
      setCurrentFile(file.name);
      setError(null);
      setResult(null);

      // Simular progreso de upload
      setProgress(30);

      setStatus('processing');
      setProgress(50);

      // Llamar al servicio
      const processedResult = await processingService.processDocument(file);

      setProgress(100);
      setStatus('success');
      setResult(processedResult);
    } catch (err: any) {
      console.error('Error procesando documento:', err);
      setStatus('error');
      setError(err.response?.data?.error || err.message || 'Error al procesar el documento');
      setProgress(0);
    }
  }, []);

  /**
   * Procesar múltiples documentos de una persona
   */
  const processPersonDocuments = useCallback(async (files: File[], metadata: EmpleadoMetadata) => {
    try {
      setStatus('uploading');
      setProgress(0);
      setCurrentFile(`${files.length} archivos`);
      setError(null);
      setResult(null);

      // Simular progreso de upload
      const uploadProgress = 30;
      setProgress(uploadProgress);

      setStatus('processing');

      // Procesar por lotes si son muchos archivos
      const batchSize = 5;
      let processed = 0;

      for (let i = 0; i < files.length; i += batchSize) {
        const batch = files.slice(i, i + batchSize);
        setCurrentFile(`Procesando ${i + 1}-${Math.min(i + batchSize, files.length)} de ${files.length}`);

        // Calcular progreso
        const progressPerFile = (100 - uploadProgress) / files.length;
        setProgress(uploadProgress + processed * progressPerFile);

        processed += batch.length;
      }

      // Llamar al servicio con todos los archivos y metadata
      const consolidatedResult = await processingService.processPersonDocuments(files, metadata);

      setProgress(100);
      setStatus('success');
      setResult(consolidatedResult);
    } catch (err: any) {
      console.error('Error procesando documentos:', err);
      setStatus('error');
      setError(err.response?.data?.error || err.message || 'Error al procesar los documentos');
      setProgress(0);
    }
  }, []);

  /**
   * Resetear el estado
   */
  const reset = useCallback(() => {
    setStatus('idle');
    setProgress(0);
    setCurrentFile(null);
    setError(null);
    setResult(null);
  }, []);

  const value: ProcessingState = {
    status,
    progress,
    currentFile,
    error,
    result,
    processDocument,
    processPersonDocuments,
    reset,
  };

  return <ProcessingContext.Provider value={value}>{children}</ProcessingContext.Provider>;
};

/**
 * Hook para usar el contexto de procesamiento
 */
export const useProcessing = (): ProcessingState => {
  const context = useContext(ProcessingContext);
  if (context === undefined) {
    throw new Error('useProcessing must be used within a ProcessingProvider');
  }
  return context;
};
