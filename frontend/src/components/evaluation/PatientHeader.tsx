import React from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { PersonOutline, Work, Business, CalendarToday } from '@mui/icons-material';

interface PatientHeaderProps {
  datos_empleado: {
    nombre_completo?: string;
    tipo_documento?: string;
    documento?: string;
    edad?: number;
    cargo?: string;
    empresa?: string;
  };
  tipo_emo?: string;
  fecha_emo?: string;
  fecha_procesamiento?: string; // Fallback si fecha_emo es null
}

const PatientHeader: React.FC<PatientHeaderProps> = ({
  datos_empleado,
  tipo_emo,
  fecha_emo,
  fecha_procesamiento,
}) => {
  const formatDocumento = () => {
    const tipo = datos_empleado.tipo_documento || '';
    const numero = datos_empleado.documento || '';

    // Si falta todo, mostrar "No especificado"
    if (!tipo && !numero) return 'No especificado';

    // Si hay tipo y número, mostrar ambos (ej: CC 1143129524)
    if (tipo && numero) return `${tipo} ${numero}`;

    // Si solo hay número, mostrarlo
    return numero;
  };

  const formatTipoEmo = (tipo?: string) => {
    if (!tipo) return 'No especificado';
    const tipos: Record<string, string> = {
      'preingreso': 'Preingreso',
      'periodico': 'Periódico',
      'post_incapacidad': 'Post-incapacidad',
      'cambio_ocupacion': 'Cambio de ocupación',
      'retiro': 'Retiro/Egreso',
    };
    return tipos[tipo] || tipo;
  };

  const formatFecha = () => {
    // Usar fecha_emo primero, si no existe, usar fecha_procesamiento como fallback
    const fechaFinal = fecha_emo || fecha_procesamiento;

    if (!fechaFinal) return 'No especificada';

    try {
      return new Date(fechaFinal).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return fechaFinal;
    }
  };

  return (
    <Box
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
    >
      {/* Nombre principal */}
      <Typography variant="h4" className="font-semibold text-gray-900 mb-4">
        {datos_empleado.nombre_completo || 'Paciente sin nombre'}
      </Typography>

      {/* Datos secundarios en grid */}
      <Box className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Documento */}
        <Box className="flex items-center gap-2">
          <PersonOutline className="text-gray-400" fontSize="small" />
          <Box>
            <Typography variant="caption" className="text-gray-500 block">
              Documento
            </Typography>
            <Typography variant="body2" className="text-gray-900 font-medium">
              {formatDocumento()}
            </Typography>
          </Box>
        </Box>

        {/* Edad */}
        {datos_empleado.edad && (
          <Box className="flex items-center gap-2">
            <PersonOutline className="text-gray-400" fontSize="small" />
            <Box>
              <Typography variant="caption" className="text-gray-500 block">
                Edad
              </Typography>
              <Typography variant="body2" className="text-gray-900 font-medium">
                {datos_empleado.edad} años
              </Typography>
            </Box>
          </Box>
        )}

        {/* Cargo */}
        {datos_empleado.cargo && (
          <Box className="flex items-center gap-2">
            <Work className="text-gray-400" fontSize="small" />
            <Box>
              <Typography variant="caption" className="text-gray-500 block">
                Cargo
              </Typography>
              <Typography variant="body2" className="text-gray-900 font-medium">
                {datos_empleado.cargo}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Empresa */}
        {datos_empleado.empresa && (
          <Box className="flex items-center gap-2">
            <Business className="text-gray-400" fontSize="small" />
            <Box>
              <Typography variant="caption" className="text-gray-500 block">
                Empresa
              </Typography>
              <Typography variant="body2" className="text-gray-900 font-medium">
                {datos_empleado.empresa}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Tipo EMO */}
        <Box className="flex items-center gap-2">
          <CalendarToday className="text-gray-400" fontSize="small" />
          <Box>
            <Typography variant="caption" className="text-gray-500 block">
              Tipo de EMO
            </Typography>
            <Chip
              label={formatTipoEmo(tipo_emo)}
              size="small"
              className="bg-blue-50 text-blue-700"
            />
          </Box>
        </Box>

        {/* Fecha EMO */}
        <Box className="flex items-center gap-2">
          <CalendarToday className="text-gray-400" fontSize="small" />
          <Box>
            <Typography variant="caption" className="text-gray-500 block">
              Fecha
            </Typography>
            <Typography variant="body2" className="text-gray-900 font-medium">
              {formatFecha()}
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default PatientHeader;
