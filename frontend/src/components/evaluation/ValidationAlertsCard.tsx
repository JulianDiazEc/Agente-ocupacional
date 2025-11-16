import React from 'react';
import { Box, Typography, Card, CardContent, Chip } from '@mui/material';
import {
  ErrorOutline,
  WarningAmber,
  InfoOutlined,
} from '@mui/icons-material';

interface Alerta {
  tipo?: string;
  severidad?: 'alta' | 'media' | 'baja';
  mensaje?: string;
  campo_afectado?: string;
}

interface ValidationAlertsCardProps {
  alertas?: Alerta[];
}

const ValidationAlertsCard: React.FC<ValidationAlertsCardProps> = ({
  alertas = [],
}) => {
  if (!alertas || alertas.length === 0) {
    return null;
  }

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
    alta: alertas.filter((a) => a.severidad === 'alta'),
    media: alertas.filter((a) => a.severidad === 'media'),
    baja: alertas.filter((a) => a.severidad === 'baja'),
  };

  return (
    <Card className="shadow-sm border border-gray-200">
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
          {/* Alertas de severidad alta */}
          {alertasPorSeveridad.alta.map((alerta, index) => {
            const config = getSeverityConfig(alerta.severidad);
            return (
              <Box
                key={`alta-${index}`}
                className={`${config.bgColor} border-l-4 ${config.borderColor} rounded-r p-3`}
              >
                <Box className="flex items-start gap-3">
                  {config.icon}
                  <Box className="flex-1">
                    <Box className="flex items-center gap-2 mb-1">
                      <Typography
                        variant="subtitle2"
                        className={`font-semibold ${config.color}`}
                      >
                        {formatCampo(alerta.campo_afectado) || formatTipo(alerta.tipo)}
                      </Typography>
                      <Chip
                        label={config.label}
                        size="small"
                        color={config.chipColor}
                      />
                    </Box>
                    <Typography variant="body2" className="text-gray-700">
                      {alerta.mensaje}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            );
          })}

          {/* Alertas de severidad media */}
          {alertasPorSeveridad.media.map((alerta, index) => {
            const config = getSeverityConfig(alerta.severidad);
            return (
              <Box
                key={`media-${index}`}
                className={`${config.bgColor} border-l-4 ${config.borderColor} rounded-r p-3`}
              >
                <Box className="flex items-start gap-3">
                  {config.icon}
                  <Box className="flex-1">
                    <Box className="flex items-center gap-2 mb-1">
                      <Typography
                        variant="subtitle2"
                        className={`font-semibold ${config.color}`}
                      >
                        {formatCampo(alerta.campo_afectado) || formatTipo(alerta.tipo)}
                      </Typography>
                      <Chip
                        label={config.label}
                        size="small"
                        color={config.chipColor}
                      />
                    </Box>
                    <Typography variant="body2" className="text-gray-700">
                      {alerta.mensaje}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            );
          })}

          {/* Alertas de severidad baja */}
          {alertasPorSeveridad.baja.map((alerta, index) => {
            const config = getSeverityConfig(alerta.severidad);
            return (
              <Box
                key={`baja-${index}`}
                className={`${config.bgColor} border-l-4 ${config.borderColor} rounded-r p-3`}
              >
                <Box className="flex items-start gap-3">
                  {config.icon}
                  <Box className="flex-1">
                    <Box className="flex items-center gap-2 mb-1">
                      <Typography
                        variant="subtitle2"
                        className={`font-semibold ${config.color}`}
                      >
                        {formatCampo(alerta.campo_afectado) || formatTipo(alerta.tipo)}
                      </Typography>
                      <Chip
                        label={config.label}
                        size="small"
                        color={config.chipColor}
                      />
                    </Box>
                    <Typography variant="body2" className="text-gray-700">
                      {alerta.mensaje}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            );
          })}
        </Box>
      </CardContent>
    </Card>
  );
};

export default ValidationAlertsCard;
