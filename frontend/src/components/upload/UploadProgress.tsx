import React from 'react';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface UploadProgressProps {
  progress: number; // 0-100
  currentFile?: string;
  totalFiles?: number;
  processedFiles?: number;
  status?: 'uploading' | 'processing' | 'success' | 'error';
  message?: string;
  className?: string;
}

/**
 * Indicador de progreso de upload/procesamiento
 * Muestra barra de progreso y estado actual
 */
export const UploadProgress: React.FC<UploadProgressProps> = ({
  progress,
  currentFile,
  totalFiles,
  processedFiles = 0,
  status = 'uploading',
  message,
  className = '',
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'success':
        return {
          icon: <CheckCircle size={24} className="text-green-500" />,
          bgColor: 'bg-green-500',
          textColor: 'text-green-700',
          title: 'Procesamiento completado',
        };
      case 'error':
        return {
          icon: <AlertCircle size={24} className="text-red-500" />,
          bgColor: 'bg-red-500',
          textColor: 'text-red-700',
          title: 'Error en el procesamiento',
        };
      case 'processing':
        return {
          icon: <Loader2 size={24} className="text-pink-500 animate-spin" />,
          bgColor: 'bg-pink-500',
          textColor: 'text-pink-700',
          title: 'Procesando documentos...',
        };
      default: // uploading
        return {
          icon: <Loader2 size={24} className="text-blue-500 animate-spin" />,
          bgColor: 'bg-blue-500',
          textColor: 'text-blue-700',
          title: 'Cargando archivos...',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        {config.icon}
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{config.title}</h3>
          {message && (
            <p className="text-sm text-gray-600 mt-0.5">{message}</p>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-gray-600">
            {status === 'success' ? 'Completado' : `Progreso: ${Math.round(progress)}%`}
          </span>
          {totalFiles && (
            <span className="text-gray-600">
              {processedFiles} de {totalFiles} archivos
            </span>
          )}
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${config.bgColor}`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Current File */}
      {currentFile && status !== 'success' && status !== 'error' && (
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-xs text-gray-500 mb-1">Procesando:</p>
          <p className="text-sm text-gray-900 font-medium truncate">
            {currentFile}
          </p>
        </div>
      )}

      {/* Success/Error Details */}
      {status === 'success' && totalFiles && (
        <div className="bg-green-50 rounded-lg p-3 border border-green-200">
          <p className="text-sm text-green-800">
            ✓ {totalFiles} documento{totalFiles > 1 ? 's' : ''} procesado{totalFiles > 1 ? 's' : ''} exitosamente
          </p>
        </div>
      )}

      {status === 'error' && message && (
        <div className="bg-red-50 rounded-lg p-3 border border-red-200">
          <p className="text-sm text-red-800">{message}</p>
        </div>
      )}
    </div>
  );
};

export default UploadProgress;
