import React from 'react';
import { Box, Typography, Card, CardContent, Chip } from '@mui/material';

interface AptitudeSummaryCardProps {
  aptitud_laboral?: string;
  tipo_emo?: string;
  confianza_extraccion?: number;
}

const AptitudeSummaryCard: React.FC<AptitudeSummaryCardProps> = ({
  aptitud_laboral,
  tipo_emo,
  confianza_extraccion,
}) => {
  // Mapeo directo sin interpretación
  const formatAptitud = (aptitud?: string) => {
    if (!aptitud) return 'No especificado';

    const aptitudMap: Record<string, string> = {
      'apto': 'Apto',
      'apto_sin_restricciones': 'Apto',
      'apto_con_recomendaciones': 'Apto con recomendaciones',
      'apto_con_restricciones': 'Apto con restricciones',
      'no_apto_temporal': 'No apto temporal',
      'no_apto_definitivo': 'No apto definitivo',
      'pendiente': 'Pendiente',
    };

    return aptitudMap[aptitud] || aptitud;
  };

  const getAptitudColor = (aptitud?: string) => {
    if (!aptitud) return 'default';

    if (aptitud === 'apto' || aptitud === 'apto_sin_restricciones') {
      return 'success';
    }
    if (aptitud === 'apto_con_recomendaciones' || aptitud === 'apto_con_restricciones') {
      return 'warning';
    }
    if (aptitud.startsWith('no_apto')) {
      return 'error';
    }
    return 'default';
  };

  const formatTipoEmo = (tipo?: string) => {
    if (!tipo) return 'EMO';
    const tipos: Record<string, string> = {
      preingreso: 'Preingreso',
      periodico: 'Periódico',
      post_incapacidad: 'Post-incapacidad',
      cambio_ocupacion: 'Cambio de ocupación',
      retiro: 'Retiro',
    };
    return tipos[tipo] || tipo;
  };

  return (
    <Card className="shadow-sm border border-gray-200 mb-6">
      <CardContent className="p-6">
        <Typography variant="h6" className="font-semibold text-gray-900 mb-4">
          Aptitud Laboral
        </Typography>

        <Box className="flex items-center gap-4">
          <Chip
            label={formatAptitud(aptitud_laboral)}
            color={getAptitudColor(aptitud_laboral) as any}
            size="medium"
          />
          <Typography variant="body2" className="text-gray-600">
            {formatTipoEmo(tipo_emo)} · Confianza:{' '}
            {confianza_extraccion
              ? `${(confianza_extraccion * 100).toFixed(0)}%`
              : 'N/A'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default AptitudeSummaryCard;
