/**
 * Página de carga de documentos
 * Permite subir PDFs individuales o múltiples para consolidación
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, Users, AlertCircle } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Alert } from '@/components/common/Alert';
import { FileDropzone } from '@/components/upload/FileDropzone';
import { FileList } from '@/components/upload/FileList';
import { UploadProgress } from '@/components/upload/UploadProgress';
import { useProcessing } from '@/contexts';

/**
 * Tipo de carga
 */
type UploadMode = 'single' | 'multiple';

/**
 * Componente UploadPage
 */
export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { status, progress, currentFile, error, result, processDocument, processPersonDocuments, reset } =
    useProcessing();

  const [mode, setMode] = useState<UploadMode>('single');
  const [files, setFiles] = useState<File[]>([]);
  const [personId, setPersonId] = useState('');

  /**
   * Manejar cambio de archivos
   */
  const handleFilesChange = (newFiles: File[]) => {
    setFiles(newFiles);
  };

  /**
   * Remover un archivo
   */
  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  /**
   * Procesar archivos
   */
  const handleProcess = async () => {
    if (files.length === 0) return;

    if (mode === 'single' && files.length === 1) {
      await processDocument(files[0]);
    } else {
      await processPersonDocuments(files, personId || undefined);
    }
  };

  /**
   * Reiniciar después de éxito
   */
  const handleReset = () => {
    reset();
    setFiles([]);
    setPersonId('');
  };

  /**
   * Ver resultado
   */
  const handleViewResult = () => {
    if (result && 'id_procesamiento' in result) {
      navigate(`/results/${result.id_procesamiento}`);
    }
  };

  /**
   * Redirigir al ver resultado exitoso
   */
  useEffect(() => {
    if (status === 'success' && result) {
      // Auto-redirigir después de 2 segundos
      const timer = setTimeout(() => {
        handleViewResult();
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [status, result]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-pink-100 rounded-full mb-3">
          <Upload className="w-6 h-6 text-pink-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Cargar Historias Clínicas
        </h1>
        <p className="text-gray-600">
          Sube documentos PDF para procesarlos con IA
        </p>
      </div>

      {/* Modo de carga */}
      <Card variant="outlined">
        <div className="flex items-center justify-center gap-4">
          <Button
            variant={mode === 'single' ? 'primary' : 'outline'}
            icon={<FileText />}
            onClick={() => {
              setMode('single');
              setFiles([]);
            }}
            disabled={status === 'uploading' || status === 'processing'}
          >
            Documento Individual
          </Button>
          <Button
            variant={mode === 'multiple' ? 'primary' : 'outline'}
            icon={<Users />}
            onClick={() => {
              setMode('multiple');
              setFiles([]);
            }}
            disabled={status === 'uploading' || status === 'processing'}
          >
            Múltiples Documentos (Consolidado)
          </Button>
        </div>
      </Card>

      {/* Info del modo */}
      {mode === 'multiple' && (
        <Alert severity="baja" icon={<AlertCircle />}>
          <p className="font-medium">Modo Consolidado</p>
          <p className="text-sm mt-1">
            Sube múltiples documentos de la misma persona para consolidar la información en una sola
            historia clínica.
          </p>
        </Alert>
      )}

      {/* Person ID (solo para múltiples) */}
      {mode === 'multiple' && (
        <Card variant="outlined">
          <div>
            <label htmlFor="personId" className="block text-sm font-medium text-gray-700 mb-2">
              ID de Persona (opcional)
            </label>
            <input
              type="text"
              id="personId"
              value={personId}
              onChange={(e) => setPersonId(e.target.value)}
              placeholder="Ej: 123456789"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              disabled={status === 'uploading' || status === 'processing'}
            />
            <p className="text-xs text-gray-500 mt-1">
              Opcional: Identificador único para agrupar documentos de la misma persona
            </p>
          </div>
        </Card>
      )}

      {/* Dropzone */}
      {status !== 'success' && (
        <FileDropzone
          maxFiles={mode === 'single' ? 1 : 10}
          onFilesChange={handleFilesChange}
          disabled={status === 'uploading' || status === 'processing'}
        />
      )}

      {/* Lista de archivos */}
      {files.length > 0 && status !== 'success' && (
        <Card variant="outlined" title="Archivos seleccionados">
          <FileList
            files={files}
            onRemove={handleRemoveFile}
            disabled={status === 'uploading' || status === 'processing'}
          />
        </Card>
      )}

      {/* Progreso */}
      {(status === 'uploading' || status === 'processing') && (
        <UploadProgress
          progress={progress}
          status={status}
          currentFile={currentFile || undefined}
          totalFiles={files.length}
        />
      )}

      {/* Error */}
      {status === 'error' && error && (
        <Alert severity="alta" closeable onClose={handleReset}>
          <p className="font-medium">Error al procesar</p>
          <p className="text-sm mt-1">{error}</p>
        </Alert>
      )}

      {/* Success */}
      {status === 'success' && result && (
        <Card variant="filled" className="bg-green-50 border-green-200">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-3">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-green-900 mb-2">
              ¡Procesamiento Exitoso!
            </h3>
            <p className="text-green-700 mb-4">
              {mode === 'single'
                ? 'El documento ha sido procesado correctamente'
                : `Se procesaron ${files.length} documentos y se consolidó la información`}
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="primary" onClick={handleViewResult}>
                Ver Resultado
              </Button>
              <Button variant="outline" onClick={handleReset}>
                Procesar Otro
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Botón de procesamiento */}
      {files.length > 0 && status !== 'success' && status !== 'uploading' && status !== 'processing' && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="primary"
            size="lg"
            icon={<Upload />}
            onClick={handleProcess}
            disabled={files.length === 0}
          >
            Procesar {files.length} {files.length === 1 ? 'Documento' : 'Documentos'}
          </Button>
          {files.length > 0 && (
            <Button variant="outline" size="lg" onClick={() => setFiles([])}>
              Limpiar
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default UploadPage;
