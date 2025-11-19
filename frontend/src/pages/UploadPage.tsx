/**
 * Página de carga de documentos
 * Enfocada en consolidación de múltiples documentos por persona
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Alert } from '@/components/common/Alert';
import { FileDropzone } from '@/components/upload/FileDropzone';
import { FileList } from '@/components/upload/FileList';
import { UploadProgress } from '@/components/upload/UploadProgress';
import { useProcessing } from '@/contexts';
import { empresaApi } from '@modules/empresa/services/empresaApi';
import { EmpresaBase, EmpresaDetail } from '@modules/empresa/types';

/**
 * Componente UploadPage
 */
export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { status, progress, currentFile, error, result, processPersonDocuments, reset } =
    useProcessing();

  const [files, setFiles] = useState<File[]>([]);
  const [empresas, setEmpresas] = useState<EmpresaBase[]>([]);
  const [empresaId, setEmpresaId] = useState('');
  const [empresaDetail, setEmpresaDetail] = useState<EmpresaDetail | null>(null);
  const [gesId, setGesId] = useState('');
  const [cargo, setCargo] = useState('');
  const [documento, setDocumento] = useState('');
  const [empresasLoading, setEmpresasLoading] = useState(true);
  const [empresaDetailLoading, setEmpresaDetailLoading] = useState(false);
  const [empresaError, setEmpresaError] = useState<string | null>(null);

  const selectedGes = useMemo(() => {
    if (!empresaDetail || !gesId) return null;
    return empresaDetail.ges.find((ges) => ges.id === gesId) || null;
  }, [empresaDetail, gesId]);

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
    if (files.length === 0 || !empresaDetail || !empresaId) return;
    await processPersonDocuments(files, {
      empresaId,
      empresaNombre: empresaDetail.nombre,
      documento,
      gesId: gesId || undefined,
      cargo: cargo || undefined,
    });
  };

  /**
   * Reiniciar después de éxito
   */
  const handleReset = () => {
    reset();
    setFiles([]);
    setDocumento('');
    setGesId('');
    setCargo('');
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

  /**
   * Cargar empresas al iniciar
   */
  useEffect(() => {
    const fetchEmpresas = async () => {
      setEmpresasLoading(true);
      setEmpresaError(null);
      try {
        const data = await empresaApi.getEmpresas();
        setEmpresas(data);
        setEmpresaId((prev) => prev || (data[0]?.id || ''));
      } catch (err) {
        console.error('Error cargando empresas', err);
        setEmpresaError('No se pudieron cargar las empresas disponibles');
      } finally {
        setEmpresasLoading(false);
      }
    };

    fetchEmpresas();
  }, []);

  /**
   * Cargar detalle de la empresa seleccionada
   */
  useEffect(() => {
    const fetchDetalle = async () => {
      if (!empresaId) {
        setEmpresaDetail(null);
        setGesId('');
        setCargo('');
        return;
      }
      setEmpresaDetailLoading(true);
      setEmpresaError(null);
      try {
        const detail = await empresaApi.getEmpresa(empresaId);
        setEmpresaDetail(detail);
        setGesId((prev) => {
          if (prev && detail.ges.some((ges) => ges.id === prev)) {
            return prev;
          }
          return detail.ges[0]?.id || '';
        });
      } catch (err) {
        console.error('Error cargando detalle de empresa', err);
        setEmpresaDetail(null);
        setGesId('');
        setCargo('');
        setEmpresaError('No se pudo cargar la información de la empresa seleccionada');
      } finally {
        setEmpresaDetailLoading(false);
      }
    };

    fetchDetalle();
  }, [empresaId]);

  /**
   * Ajustar cargo cuando cambia el GES
   */
  useEffect(() => {
    if (!selectedGes) {
      setCargo('');
      return;
    }
    const cargosDisponibles = selectedGes.cargos || [];
    if (cargosDisponibles.length === 0) {
      setCargo('');
      return;
    }
    setCargo((prev) => (prev && cargosDisponibles.includes(prev) ? prev : cargosDisponibles[0]));
  }, [selectedGes]);

  const empresaListaVacia = !empresasLoading && empresas.length === 0;
  const empresaSeleccionadaNombre = empresaDetail?.nombre || '';
  const puedeProcesar =
    files.length > 0 && !!documento.trim() && !!empresaId && !!empresaSeleccionadaNombre;

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
          currentFile={currentFile || undefined}
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
              {empresasLoading ? (
                <p className="text-sm text-gray-500">Cargando empresas...</p>
              ) : empresaListaVacia ? (
                <p className="text-sm text-gray-500">No hay empresas configuradas aún.</p>
              ) : (
                <select
                  value={empresaId}
                  onChange={(e) => setEmpresaId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {empresas.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nombre}
                    </option>
                  ))}
                </select>
              )}
              <p className="text-xs text-gray-500 mt-1">Selecciona la empresa del empleado</p>
              {empresaError && (
                <p className="text-xs text-red-600 mt-1">{empresaError}</p>
              )}
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Grupo de exposición (GES)
              </label>
              {empresaDetailLoading ? (
                <p className="text-sm text-gray-500">Cargando información de la empresa...</p>
              ) : !empresaDetail ? (
                <p className="text-sm text-gray-500">Selecciona una empresa para ver sus GES.</p>
              ) : empresaDetail.ges.length === 0 ? (
                <p className="text-sm text-gray-500">Esta empresa no tiene GES configurados.</p>
              ) : (
                <select
                  value={gesId}
                  onChange={(e) => setGesId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {empresaDetail.ges.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nombre}
                    </option>
                  ))}
                </select>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Elige el grupo de exposición similar asociado al empleado
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cargo asociado
              </label>
              {selectedGes && (selectedGes.cargos?.length || 0) > 0 ? (
                <select
                  value={cargo}
                  onChange={(e) => setCargo(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {(selectedGes.cargos || []).map((cargoItem) => (
                    <option key={cargoItem} value={cargoItem}>
                      {cargoItem}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-sm text-gray-500">
                  No hay cargos asociados al GES seleccionado. Se enviará vacío.
                </p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Se enviará junto con los archivos para enriquecer el consolidado
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
                disabled={!puedeProcesar}
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
