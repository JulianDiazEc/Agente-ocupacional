/**
 * Página de detalle de resultado
 * Muestra información completa de una historia clínica procesada
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, FileText, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Alert } from '@/components/common/Alert';
import { PatientInfo } from '@/components/results/PatientInfo';
import { DiagnosticsList } from '@/components/results/DiagnosticsList';
import { ExamResults } from '@/components/results/ExamResults';
import { useResults } from '@/contexts';
import { exportService } from '@/services';

/**
 * Componente ResultDetailPage
 */
export const ResultDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedResult, loading, error, fetchResultById, selectResult } = useResults();
  const [exporting, setExporting] = useState(false);

  /**
   * Cargar resultado al montar
   */
  useEffect(() => {
    if (id) {
      fetchResultById(id);
    }

    return () => {
      selectResult(null);
    };
  }, [id, fetchResultById, selectResult]);

  /**
   * Exportar a JSON
   */
  const handleExportJSON = async () => {
    if (!selectedResult) return;
    setExporting(true);
    try {
      await exportService.exportToJSON(selectedResult);
    } catch (err) {
      console.error('Error exportando:', err);
    } finally {
      setExporting(false);
    }
  };

  /**
   * Exportar a Excel
   */
  const handleExportExcel = async () => {
    if (!selectedResult) return;
    setExporting(true);
    try {
      await exportService.exportToExcel([selectedResult.id_procesamiento]);
    } catch (err) {
      console.error('Error exportando:', err);
    } finally {
      setExporting(false);
    }
  };

  /**
   * Get badge para aptitud
   */
  const getAptitudBadge = () => {
    if (!selectedResult) return null;

    const { resultado_aptitud } = selectedResult.aptitud_laboral;

    switch (resultado_aptitud) {
      case 'apto':
        return <Badge variant="success" icon={<CheckCircle />}>Apto</Badge>;
      case 'apto_con_restricciones':
        return <Badge variant="warning" icon={<AlertTriangle />}>Apto con Restricciones</Badge>;
      case 'no_apto_temporal':
        return <Badge variant="error" icon={<XCircle />}>No Apto Temporal</Badge>;
      case 'no_apto_permanente':
        return <Badge variant="error" icon={<XCircle />}>No Apto Permanente</Badge>;
      default:
        return <Badge variant="default">Pendiente</Badge>;
    }
  };

  /**
   * Loading
   */
  if (loading) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Cargando resultado...</p>
      </div>
    );
  }

  /**
   * Error
   */
  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <Alert severity="alta">
          <p className="font-medium">Error al cargar el resultado</p>
          <p className="text-sm mt-1">{error}</p>
        </Alert>
        <div className="mt-6 text-center">
          <Button variant="outline" icon={<ArrowLeft />} onClick={() => navigate('/results')}>
            Volver a Resultados
          </Button>
        </div>
      </div>
    );
  }

  /**
   * No encontrado
   */
  if (!selectedResult) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Resultado no encontrado</h2>
        <p className="text-gray-600 mb-6">El resultado que buscas no existe o ha sido eliminado</p>
        <Button variant="outline" icon={<ArrowLeft />} onClick={() => navigate('/results')}>
          Volver a Resultados
        </Button>
      </div>
    );
  }

  const alertasAltas = selectedResult.alertas_validacion.filter((a) => a.severidad === 'alta');
  const alertasMedias = selectedResult.alertas_validacion.filter((a) => a.severidad === 'media');
  const alertasBajas = selectedResult.alertas_validacion.filter((a) => a.severidad === 'baja');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            icon={<ArrowLeft />}
            onClick={() => navigate('/results')}
            className="flex-shrink-0"
          >
            Volver
          </Button>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
              {selectedResult.datos_empleado.nombre_completo}
            </h1>
            <p className="text-gray-600">
              {selectedResult.datos_empleado.documento} • {selectedResult.tipo_emo}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            icon={<Download />}
            onClick={handleExportJSON}
            disabled={exporting}
          >
            JSON
          </Button>
          <Button
            variant="outline"
            icon={<Download />}
            onClick={handleExportExcel}
            disabled={exporting}
          >
            Excel
          </Button>
        </div>
      </div>

      {/* Aptitud y Confianza */}
      <Card variant="outlined">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Aptitud Laboral</p>
            {getAptitudBadge()}
            {selectedResult.aptitud_laboral.recomendaciones && (
              <p className="text-sm text-gray-600 mt-2">
                {selectedResult.aptitud_laboral.recomendaciones}
              </p>
            )}
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600 mb-1">Confianza de Extracción</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden min-w-[100px]">
                <div
                  className={`h-full ${
                    selectedResult.confianza_extraccion >= 90
                      ? 'bg-green-500'
                      : selectedResult.confianza_extraccion >= 70
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${selectedResult.confianza_extraccion}%` }}
                />
              </div>
              <span className="text-lg font-semibold text-gray-900">
                {selectedResult.confianza_extraccion}%
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Alertas de Validación */}
      {selectedResult.alertas_validacion.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">Alertas de Validación</h2>

          {alertasAltas.map((alerta, idx) => (
            <Alert key={`alta-${idx}`} severity="alta" icon={<AlertTriangle />}>
              <p className="font-medium">{alerta.campo}</p>
              <p className="text-sm mt-1">{alerta.mensaje}</p>
            </Alert>
          ))}

          {alertasMedias.map((alerta, idx) => (
            <Alert key={`media-${idx}`} severity="media" icon={<AlertTriangle />}>
              <p className="font-medium">{alerta.campo}</p>
              <p className="text-sm mt-1">{alerta.mensaje}</p>
            </Alert>
          ))}

          {alertasBajas.map((alerta, idx) => (
            <Alert key={`baja-${idx}`} severity="baja" icon={<AlertTriangle />}>
              <p className="font-medium">{alerta.campo}</p>
              <p className="text-sm mt-1">{alerta.mensaje}</p>
            </Alert>
          ))}
        </div>
      )}

      {/* Información del Paciente */}
      <PatientInfo historia={selectedResult} />

      {/* Diagnósticos */}
      <DiagnosticsList diagnosticos={selectedResult.diagnosticos} />

      {/* Exámenes */}
      <ExamResults examenes={selectedResult.examenes} />

      {/* Metadata */}
      <Card variant="outlined" title="Información de Procesamiento">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-600">ID de Procesamiento</p>
            <p className="font-mono text-xs text-gray-900 mt-1">
              {selectedResult.id_procesamiento}
            </p>
          </div>
          <div>
            <p className="text-gray-600">Fecha de Procesamiento</p>
            <p className="text-gray-900 mt-1">
              {new Date(selectedResult.fecha_procesamiento).toLocaleString('es-ES')}
            </p>
          </div>
          <div>
            <p className="text-gray-600">Archivo Original</p>
            <p className="text-gray-900 mt-1 truncate">{selectedResult.archivo_origen}</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ResultDetailPage;
