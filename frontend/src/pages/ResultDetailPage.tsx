/**
 * Página de detalle de resultado - Reorganizada con Resumen Clínico
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
import ClinicalSummaryCard from '@/components/evaluation/ClinicalSummaryCard';
import ValidationAlertsCard from '@/components/evaluation/ValidationAlertsCard';

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
  };

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

      {/* 1️⃣ Header del Paciente */}
      <PatientHeader
        datos_empleado={selectedResult.datos_empleado}
        tipo_emo={selectedResult.tipo_emo}
        fecha_emo={selectedResult.fecha_emo}
      />

      {/* 2️⃣ Card Principal: Estimación de Aptitud Laboral */}
      <AptitudeSummaryCard
        aptitud_laboral={selectedResult.aptitud_laboral?.resultado_aptitud}
        tipo_emo={selectedResult.tipo_emo}
        confianza_extraccion={selectedResult.confianza_extraccion}
        diagnosticos={selectedResult.diagnosticos}
        signos_vitales={selectedResult.signos_vitales}
        examenes={selectedResult.examenes}
      />

      {/* 3️⃣ Resumen Clínico (NUEVO - reemplaza KeyFindingsCard) */}
      <Box>
        <Typography variant="h6" className="font-semibold text-gray-900 mb-4">
          Resumen Clínico
        </Typography>
        <ClinicalSummaryCard
          signos_vitales={selectedResult.signos_vitales}
          examenes={selectedResult.examenes}
          diagnosticos={selectedResult.diagnosticos}
          antecedentes={selectedResult.antecedentes}
        />
      </Box>

      {/* 4️⃣ Alertas de Validación (MOVIDO aquí, mejorado con colapsables) */}
      <ValidationAlertsCard alertas={selectedResult.alertas_validacion} />

      {/* 5️⃣ Metadata de procesamiento (al final) */}
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
