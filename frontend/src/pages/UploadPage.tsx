/**
 * Página de carga de documentos
 * Enfocada en consolidación de múltiples documentos por persona
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Alert } from '@/components/common/Alert';
import { FileDropzone } from '@/components/upload/FileDropzone';
import { FileList } from '@/components/upload/FileList';
import { UploadProgress } from '@/components/upload/UploadProgress';
import { useProcessing } from '@/contexts';

/**
 * Componente UploadPage
 */
export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { status, progress, currentFile, error, result, processPersonDocuments, reset } =
    useProcessing();

  const [files, setFiles] = useState<File[]>([]);
  const [personId, setPersonId] = useState('');
  const [empresa, setEmpresa] = useState('Fundación Ser Social');
  const [documento, setDocumento] = useState('');

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
    await processPersonDocuments(files, {
      personId: personId || undefined,
      empresa,
      documento,
    });
  };

  /**
   * Reiniciar después de éxito
   */
  const handleReset = () => {
    reset();
    setFiles([]);
    setPersonId('');
    setEmpresa('Fundación Ser Social');
    setDocumento('');
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
        <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-3">
          <Upload className="w-6 h-6 text-blue-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Procesar Evaluación Médica Ocupacional
        </h1>
        <p className="text-gray-600">
          Sube uno o más documentos PDF de un paciente para generar una historia clínica consolidada
        </p>
      </div>

      {/* Estados de procesamiento */}
      {status === 'processing' && (
        <UploadProgress
          progress={progress}
          currentFile={currentFile}
          totalFiles={files.length}
        />
      )}

      {status === 'success' && (
        <Alert severity="baja">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            <p className="font-medium">¡Procesamiento exitoso!</p>
          </div>
          <p className="text-sm mt-1">
            La historia clínica consolidada ha sido procesada correctamente. Redirigiendo...
          </p>
        </Alert>
      )}

      {error && (
        <Alert severity="alta">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            <p className="font-medium">Error al procesar documentos</p>
          </div>
          <p className="text-sm mt-1">{error}</p>
        </Alert>
      )}

      {/* Formulario de carga */}
      {status === 'idle' && (
        <>
          <Card variant="outlined">
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Empresa <span className="text-red-500">*</span>
              </label>
              <select
                value={empresa}
                onChange={(e) => setEmpresa(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="Fundación Ser Social">Fundación Ser Social</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Selecciona la empresa del empleado
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Documento del Empleado <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={documento}
                onChange={(e) => setDocumento(e.target.value)}
                placeholder="Ej: CC 12345678, 1234567890"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Ingresa el número de documento del empleado
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ID del Paciente (opcional)
              </label>
              <input
                type="text"
                value={personId}
                onChange={(e) => setPersonId(e.target.value)}
                placeholder="Ej: CC-12345678, HC-001"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Si no lo especificas, se generará automáticamente un ID único
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Documentos del Paciente
              </label>
              <FileDropzone
                onFilesChange={handleFilesChange}
                multiple={true}
                maxFiles={10}
              />
              <p className="text-xs text-gray-500 mt-2">
                Puedes subir hasta 10 PDFs (máx. 10MB cada uno). Todos los documentos se
                consolidarán en una única historia clínica.
              </p>
            </div>

            {files.length > 0 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Archivos seleccionados ({files.length})
                </label>
                <FileList files={files} onRemove={handleRemoveFile} />
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                {files.length > 0 ? (
                  <span className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    {files.length} documento{files.length !== 1 ? 's' : ''} listo
                    {files.length !== 1 ? 's' : ''} para procesar
                  </span>
                ) : (
                  <span className="text-gray-400">
                    Selecciona al menos un documento para comenzar
                  </span>
                )}
              </div>
              <Button
                variant="primary"
                icon={<Upload />}
                onClick={handleProcess}
                disabled={files.length === 0 || !documento.trim()}
              >
                Procesar Documentos
              </Button>
            </div>
          </Card>

          {/* Info adicional */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <svg
                  className="w-5 h-5 text-blue-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-blue-900 mb-1">
                  ¿Cómo funciona la consolidación?
                </h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Todos los documentos del paciente se procesan individualmente</li>
                  <li>• Los diagnósticos, exámenes y antecedentes se combinan</li>
                  <li>• Se eliminan duplicados y se prioriza la información más confiable</li>
                  <li>• El resultado es una historia clínica única y completa</li>
                </ul>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Acciones post-procesamiento */}
      {status === 'success' && (
        <div className="flex items-center justify-center gap-4">
          <Button variant="outline" onClick={handleReset}>
            Procesar otro paciente
          </Button>
          <Button variant="primary" onClick={handleViewResult}>
            Ver resultado ahora
          </Button>
        </div>
      )}

      {error && (
        <div className="flex items-center justify-center">
          <Button variant="outline" onClick={handleReset}>
            Reintentar
          </Button>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
