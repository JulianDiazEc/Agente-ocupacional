/**
 * Página de detalle de resultado - Diseño simplificado y elegante
 * Muestra información completa de una historia clínica procesada
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Button as MuiButton } from '@mui/material';
import { ArrowBack, Download, Description } from '@mui/icons-material';
import { Button } from '@/components/common/Button';
import { Alert } from '@/components/common/Alert';
import { useResults } from '@/contexts';
import { exportService } from '@/services';

// Componentes de evaluación
import PatientHeader from '@/components/evaluation/PatientHeader';
import AptitudeSummaryCard from '@/components/evaluation/AptitudeSummaryCard';
import UnifiedClinicalCard from '@/components/evaluation/UnifiedClinicalCard';

/**
 * Componente ResultDetailPage
 */
export const ResultDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedResult, loading, error, fetchResultById, selectResult } = useResults();
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

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
    setExportError(null);
    try {
      await exportService.exportToJSON(selectedResult);
    } catch (err: any) {
      console.error('Error exportando:', err);
      setExportError(err.message || 'Error al exportar a JSON');
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
    setExportError(null);
    try {
      await exportService.exportToExcel([selectedResult.id_procesamiento]);
    } catch (err: any) {
      console.error('Error exportando:', err);
      setExportError(err.message || 'Error al exportar a Excel');
    } finally {
      setExporting(false);
    }
  };

  /**
   * Loading
   */
  if (loading) {
    return (
      <Box className="flex flex-col items-center justify-center py-12">
        <CircularProgress size={48} className="mb-4" />
        <Typography variant="body1" className="text-gray-600">
          Cargando resultado...
        </Typography>
      </Box>
    );
  }

  /**
   * Error
   */
  if (error) {
    return (
      <Box className="max-w-2xl mx-auto">
        <Alert severity="alta">
          <p className="font-medium">Error al cargar el resultado</p>
          <p className="text-sm mt-1">{error}</p>
        </Alert>
        <Box className="mt-6 text-center">
          <MuiButton
            variant="outlined"
            startIcon={<ArrowBack />}
            onClick={() => navigate('/results')}
          >
            Volver a Resultados
          </MuiButton>
        </Box>
      </Box>
    );
  }

  /**
   * No encontrado
   */
  if (!selectedResult) {
    return (
      <Box className="max-w-2xl mx-auto text-center py-12">
        <Description sx={{ fontSize: 64, color: 'rgb(209 213 219)', mb: 2 }} />
        <Typography variant="h5" className="font-bold text-gray-900 mb-2">
          Resultado no encontrado
        </Typography>
        <Typography variant="body1" className="text-gray-600 mb-6">
          El resultado que buscas no existe o ha sido eliminado
        </Typography>
        <MuiButton
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/results')}
        >
          Volver a Resultados
        </MuiButton>
      </Box>
    );
  }

  return (
    <Box className="space-y-6">
      {/* Header con botones de acción */}
      <Box className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <Box className="flex items-center gap-3">
          <MuiButton
            variant="text"
            startIcon={<ArrowBack />}
            onClick={() => navigate('/results')}
          >
            Volver
          </MuiButton>
        </Box>
        <Box className="flex items-center gap-2">
          <MuiButton
            variant="outlined"
            startIcon={<Download />}
            onClick={handleExportJSON}
            disabled={exporting}
            size="small"
          >
            JSON
          </MuiButton>
          <MuiButton
            variant="outlined"
            startIcon={<Download />}
            onClick={handleExportExcel}
            disabled={exporting}
            size="small"
          >
            Excel
          </MuiButton>
        </Box>
      </Box>

      {/* Mensaje de error de exportación */}
      {exportError && (
        <Alert severity="alta">
          <p className="font-medium">Error de exportación</p>
          <p className="text-sm mt-1">{exportError}</p>
          <MuiButton
            variant="text"
            size="small"
            onClick={() => setExportError(null)}
            className="mt-2"
          >
            Cerrar
          </MuiButton>
        </Alert>
      )}

      {/* 1. Header del Paciente */}
      <PatientHeader
        datos_empleado={selectedResult.datos_empleado}
        tipo_emo={selectedResult.tipo_emo}
        fecha_emo={selectedResult.fecha_emo}
      />

      {/* 2. Aptitud Laboral (simplificada) */}
      <AptitudeSummaryCard
        aptitud_laboral={selectedResult.aptitud_laboral as string}
        tipo_emo={selectedResult.tipo_emo}
        confianza_extraccion={selectedResult.confianza_extraccion}
      />

      {/* 3. Resumen Clínico Unificado (hallazgos + normales + alertas) */}
      <UnifiedClinicalCard
        signos_vitales={selectedResult.signos_vitales}
        examenes={selectedResult.examenes}
        diagnosticos={selectedResult.diagnosticos}
        antecedentes={selectedResult.antecedentes}
        recomendaciones={selectedResult.recomendaciones}
        alertas={selectedResult.alertas_validacion}
      />

      {/* 4. Metadata de procesamiento */}
      <Box className="bg-gray-50 border border-gray-200 rounded-lg p-6 mt-8">
        <Typography variant="subtitle2" className="font-semibold text-gray-700 mb-4">
          Información de Procesamiento
        </Typography>
        <Box className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <Box>
            <Typography variant="caption" className="text-gray-600 block">
              ID de Procesamiento
            </Typography>
            <Typography
              variant="body2"
              className="font-mono text-xs text-gray-900 mt-1 break-all"
            >
              {selectedResult.id_procesamiento}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" className="text-gray-600 block">
              Fecha de Procesamiento
            </Typography>
            <Typography variant="body2" className="text-gray-900 mt-1">
              {new Date(selectedResult.fecha_procesamiento).toLocaleString('es-ES')}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" className="text-gray-600 block">
              Archivo Original
            </Typography>
            <Typography variant="body2" className="text-gray-900 mt-1 truncate">
              {selectedResult.archivo_origen}
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default ResultDetailPage;
