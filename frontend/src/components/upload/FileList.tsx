import React from 'react';
import { FileText, X, CheckCircle, AlertCircle } from 'lucide-react';

interface FileItem {
  file: File;
  status?: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

interface FileListProps {
  files: File[];
  onRemove?: (index: number) => void;
  statuses?: Record<number, 'pending' | 'uploading' | 'success' | 'error'>;
  errors?: Record<number, string>;
  className?: string;
}

/**
 * Lista de archivos seleccionados
 * Muestra nombre, tamaño y permite eliminar
 */
export const FileList: React.FC<FileListProps> = ({
  files,
  onRemove,
  statuses = {},
  errors = {},
  className = '',
}) => {
  if (files.length === 0) {
    return null;
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusIcon = (index: number) => {
    const status = statuses[index];

    switch (status) {
      case 'success':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'error':
        return <AlertCircle size={16} className="text-red-500" />;
      case 'uploading':
        return (
          <div className="animate-spin h-4 w-4 border-2 border-pink-500 border-t-transparent rounded-full" />
        );
      default:
        return <FileText size={16} className="text-gray-400" />;
    }
  };

  const getStatusBg = (index: number) => {
    const status = statuses[index];

    switch (status) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'uploading':
        return 'bg-pink-50 border-pink-200';
      default:
        return 'bg-white border-gray-200';
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <h4 className="text-sm font-medium text-gray-700 mb-3">
        Archivos seleccionados ({files.length})
      </h4>

      {files.map((file, index) => (
        <div
          key={`${file.name}-${index}`}
          className={`
            flex items-center justify-between gap-3 p-3 rounded-lg border
            transition-all ${getStatusBg(index)}
          `}
        >
          {/* Icon & Info */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {getStatusIcon(index)}

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {file.name}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <p className="text-xs text-gray-500">
                  {formatFileSize(file.size)}
                </p>
                {errors[index] && (
                  <>
                    <span className="text-xs text-gray-300">•</span>
                    <p className="text-xs text-red-600 truncate">
                      {errors[index]}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Remove button */}
          {onRemove && statuses[index] !== 'uploading' && (
            <button
              onClick={() => onRemove(index)}
              className="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
              title="Eliminar archivo"
            >
              <X size={16} />
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

export default FileList;
