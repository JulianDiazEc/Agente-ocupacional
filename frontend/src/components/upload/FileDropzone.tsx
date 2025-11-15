import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { FileUploadProps } from '@/types';

/**
 * Dropzone para cargar archivos PDF
 * Drag & drop con validación
 */
export const FileDropzone: React.FC<FileUploadProps> = ({
  accept = '.pdf',
  multiple = true,
  maxSize = 10, // MB
  maxFiles = 10,
  onFilesChange,
  files = [],
  error,
  disabled = false,
  className = '',
}) => {
  const [internalError, setInternalError] = useState<string>('');
  const allowedExtensions = accept
    ? accept.split(',').map((ext) => ext.trim().toLowerCase()).filter(Boolean)
    : ['.pdf'];
  const dropzoneAccept = {
    'application/pdf': allowedExtensions.length > 0 ? allowedExtensions : ['.pdf'],
  };

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setInternalError('');

      // Validar tamaño
      const oversizedFiles = acceptedFiles.filter(
        (file) => file.size > maxSize * 1024 * 1024
      );

      if (oversizedFiles.length > 0) {
        setInternalError(
          `Algunos archivos exceden el tamaño máximo de ${maxSize}MB`
        );
        return;
      }

      // Validar cantidad
      if (maxFiles && acceptedFiles.length + files.length > maxFiles) {
        setInternalError(`Máximo ${maxFiles} archivos permitidos`);
        return;
      }

      // Validar tipo
      const invalidFiles = acceptedFiles.filter(
        (file) => !allowedExtensions.some((ext) => file.name.toLowerCase().endsWith(ext))
      );

      if (invalidFiles.length > 0) {
        setInternalError('Solo se permiten archivos PDF');
        return;
      }

      // Archivos rechazados
      if (rejectedFiles.length > 0) {
        setInternalError('Algunos archivos no son válidos');
        return;
      }

      // Callback con archivos válidos
      const newFiles = [...files, ...acceptedFiles];
      onFilesChange(newFiles);
    },
    [files, maxSize, maxFiles, onFilesChange, allowedExtensions]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: dropzoneAccept,
    multiple,
    disabled,
    maxSize: maxSize * 1024 * 1024,
  });

  const displayError = error || internalError;

  return (
    <div className={className}>
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
          ${isDragActive && !isDragReject ? 'border-pink-500 bg-pink-50' : ''}
          ${isDragReject ? 'border-red-500 bg-red-50' : ''}
          ${!isDragActive && !displayError ? 'border-gray-300 hover:border-pink-400 hover:bg-pink-50/50' : ''}
          ${displayError ? 'border-red-300 bg-red-50' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />

        {/* Icon */}
        <div className="flex justify-center mb-4">
          {displayError ? (
            <AlertCircle size={48} className="text-red-500" />
          ) : files.length > 0 ? (
            <CheckCircle size={48} className="text-green-500" />
          ) : (
            <Upload size={48} className="text-gray-400" />
          )}
        </div>

        {/* Text */}
        <div className="space-y-2">
          {isDragActive && !isDragReject && (
            <p className="text-lg font-medium text-pink-600">
              Suelta los archivos aquí...
            </p>
          )}

          {isDragReject && (
            <p className="text-lg font-medium text-red-600">
              Archivo no válido
            </p>
          )}

          {!isDragActive && !displayError && (
            <>
              <p className="text-lg font-medium text-gray-900">
                {files.length > 0
                  ? `${files.length} archivo${files.length > 1 ? 's' : ''} seleccionado${files.length > 1 ? 's' : ''}`
                  : 'Arrastra tus archivos PDF aquí'}
              </p>
              <p className="text-sm text-gray-500">
                o haz clic para seleccionar
              </p>
            </>
          )}

          {displayError && (
            <p className="text-sm font-medium text-red-600">{displayError}</p>
          )}
        </div>

        {/* File info */}
        <div className="mt-4 flex items-center justify-center gap-6 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <FileText size={14} />
            Solo PDF
          </span>
          <span>Máx. {maxSize}MB</span>
          {maxFiles && <span>Hasta {maxFiles} archivos</span>}
        </div>
      </div>
    </div>
  );
};

export default FileDropzone;
