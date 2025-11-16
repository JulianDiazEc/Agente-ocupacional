import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  ErrorOutline,
  WarningAmber,
  InfoOutlined,
  ExpandMore,
  Lightbulb,
} from '@mui/icons-material';

interface Alerta {
  tipo?: string;
  severidad?: 'alta' | 'media' | 'baja';
  mensaje?: string;
  descripcion?: string;
  campo_afectado?: string;
  accion_sugerida?: string;
}

interface ValidationAlertsCardProps {
  alertas?: Alerta[];
}

const ValidationAlertsCard: React.FC<ValidationAlertsCardProps> = ({
  alertas = [],
}) => {
  const [expandedAlerts, setExpandedAlerts] = useState<Set<number>>(new Set());

  if (!alertas || alertas.length === 0) {
    return null;
  }

  const toggleAlert = (index: number) => {
    setExpandedAlerts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const getSeverityConfig = (severidad?: string) => {
    switch (severidad) {
      case 'alta':
        return {
          icon: <ErrorOutline className="text-red-600" />,
          color: 'text-red-700',
          bgColor: 'bg-red-50',
          borderColor: 'border-l-red-500',
          chipColor: 'error' as const,
          label: 'Alta',
        };
      case 'media':
        return {
          icon: <WarningAmber className="text-amber-600" />,
          color: 'text-amber-700',
          bgColor: 'bg-amber-50',
          borderColor: 'border-l-amber-500',
          chipColor: 'warning' as const,
          label: 'Media',
        };
      default:
        return {
          icon: <InfoOutlined className="text-blue-600" />,
          color: 'text-blue-700',
          bgColor: 'bg-blue-50',
          borderColor: 'border-l-blue-500',
          chipColor: 'info' as const,
          label: 'Baja',
        };
    }
  };

  const formatTipo = (tipo?: string) => {
    if (!tipo) return 'Alerta';
    const tipos: Record<string, string> = {
      inconsistencia: 'Inconsistencia',
      dato_faltante: 'Dato faltante',
      valor_critico: 'Valor crítico',
      formato_incorrecto: 'Formato incorrecto',
      validacion: 'Validación',
    };
    return tipos[tipo] || tipo;
  };

  const formatCampo = (campo?: string) => {
    if (!campo) return null;
    const campos: Record<string, string> = {
      imc: 'IMC',
      presion_arterial: 'Presión arterial',
      codigo_cie10: 'Código CIE-10',
      aptitud_laboral: 'Aptitud laboral',
      signos_vitales: 'Signos vitales',
      diagnosticos: 'Diagnósticos',
      examenes: 'Exámenes',
    };
    return campos[campo] || campo;
  };

  // Agrupar alertas por severidad
  const alertasPorSeveridad = {
    alta: alertas
      .map((a, idx) => ({ ...a, originalIndex: idx }))
      .filter((a) => a.severidad === 'alta'),
    media: alertas
      .map((a, idx) => ({ ...a, originalIndex: idx }))
      .filter((a) => a.severidad === 'media'),
    baja: alertas
      .map((a, idx) => ({ ...a, originalIndex: idx }))
      .filter((a) => a.severidad === 'baja'),
  };

  const allAlertasOrdered = [
    ...alertasPorSeveridad.alta,
    ...alertasPorSeveridad.media,
    ...alertasPorSeveridad.baja,
  ];

  return (
    <Card className="shadow-sm border border-gray-200 mb-6">
      <CardContent className="p-6">
        <Box className="flex items-center justify-between mb-4">
          <Typography variant="h6" className="font-semibold text-gray-900">
            Alertas de validación
          </Typography>
          <Chip
            label={`${alertas.length} alerta${alertas.length !== 1 ? 's' : ''}`}
            size="small"
            className="bg-gray-100 text-gray-700"
          />
        </Box>

        <Box className="space-y-3">
          {allAlertasOrdered.map((alerta, displayIndex) => {
            const config = getSeverityConfig(alerta.severidad);
            const isExpanded = expandedAlerts.has(alerta.originalIndex);

            return (
              <Box
                key={alerta.originalIndex}
                className={`${config.bgColor} border-l-4 ${config.borderColor} rounded-r transition-all`}
              >
                {/* Header colapsable */}
                <Box
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-opacity-80"
                  onClick={() => toggleAlert(alerta.originalIndex)}
                >
                  <Box className="flex items-center gap-3 flex-1">
                    {config.icon}
                    <Box className="flex items-center gap-2 flex-1">
                      <Typography
                        variant="subtitle2"
                        className={`font-semibold ${config.color}`}
                      >
                        {formatCampo(alerta.campo_afectado) ||
                          formatTipo(alerta.tipo)}
                      </Typography>
                      <Chip
                        label={config.label}
                        size="small"
                        color={config.chipColor}
                      />
                    </Box>
                  </Box>
                  <IconButton
                    size="small"
                    sx={{
                      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.3s',
                    }}
                  >
                    <ExpandMore />
                  </IconButton>
                </Box>

                {/* Contenido expandible */}
                <Collapse in={isExpanded}>
                  <Box className="px-3 pb-3 pt-1 border-t border-gray-200 mt-2">
                    {/* Descripción/Mensaje */}
                    <Typography variant="body2" className="text-gray-700 mb-2">
                      {alerta.descripcion || alerta.mensaje || 'Sin descripción'}
                    </Typography>

                    {/* Acción sugerida */}
                    {alerta.accion_sugerida && (
                      <Box className="flex items-start gap-2 mt-3 p-2 bg-white bg-opacity-50 rounded">
                        <Lightbulb
                          className="text-amber-600"
                          sx={{ fontSize: 20 }}
                        />
                        <Box>
                          <Typography
                            variant="caption"
                            className="font-semibold text-gray-600 block"
                          >
                            Acción sugerida:
                          </Typography>
                          <Typography variant="body2" className="text-gray-700">
                            {alerta.accion_sugerida}
                          </Typography>
                        </Box>
                      </Box>
                    )}
                  </Box>
                </Collapse>
              </Box>
            );
          })}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ValidationAlertsCard;
