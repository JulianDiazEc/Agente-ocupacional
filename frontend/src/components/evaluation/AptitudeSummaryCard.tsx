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
  const getAptitudLabel = () => {
    const aptitud = aptitud_laboral?.toLowerCase() || '';

    if (aptitud.includes('apto') && !aptitud.includes('restriccion')) {
      return 'Apto';
    }
    if (aptitud.includes('restriccion')) {
      return 'Apto con restricciones';
    }
    if (aptitud.includes('no_apto')) {
      return 'No apto';
    }
    return 'Pendiente';
  };

  const getAptitudColor = () => {
    const aptitud = aptitud_laboral?.toLowerCase() || '';

    if (aptitud.includes('apto') && !aptitud.includes('restriccion')) {
      return 'success';
    }
    if (aptitud.includes('restriccion')) {
      return 'warning';
    }
    if (aptitud.includes('no_apto')) {
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
            label={getAptitudLabel()}
            color={getAptitudColor() as any}
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
