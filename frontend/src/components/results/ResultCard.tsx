import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Calendar, Briefcase, AlertCircle, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/common';
import { HistoriaClinicaProcesada } from '@/types';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

interface ResultCardProps {
  historia: HistoriaClinicaProcesada;
  onClick?: () => void;
  className?: string;
}

/**
 * Card de resultado de HC procesada
 * Vista resumida para lista de resultados
 */
export const ResultCard: React.FC<ResultCardProps> = ({
  historia,
  onClick,
  className = '',
}) => {
  const navigate = useNavigate();

  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/results/${historia.id_procesamiento}`);
    }
  };

  // Aptitud badge variant
  const getAptitudBadge = () => {
    // Manejo defensivo: puede ser null, undefined, string, u objeto
    if (!historia.aptitud_laboral) {
      return { variant: 'default' as const, label: 'Pendiente' };
    }

    const resultado =
      typeof historia.aptitud_laboral === 'string'
        ? historia.aptitud_laboral
        : historia.aptitud_laboral.resultado_aptitud;

    switch (resultado as string) {
      case 'apto':
      case 'apto_sin_restricciones':
        return { variant: 'success' as const, label: 'Apto' };
      case 'apto_con_recomendaciones':
      case 'apto_con_restricciones':
        return { variant: 'warning' as const, label: 'Apto con restricciones' };
      case 'no_apto_temporal':
        return { variant: 'warning' as const, label: 'No apto temporal' };
      case 'no_apto_definitivo':
      case 'no_apto_permanente':
        return { variant: 'error' as const, label: 'No apto definitivo' };
      default:
        return { variant: 'default' as const, label: 'Pendiente' };
    }
  };

  const aptitudBadge = getAptitudBadge();

  // Confianza color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Alertas altas (manejo defensivo)
  const alertasAltas = (historia.alertas_validacion || []).filter(a => a.severidad === 'alta').length;

  return (
    <div
      onClick={handleClick}
      className={`
        bg-white rounded-xl border border-gray-200 p-5 cursor-pointer
        transition-all duration-200 hover:shadow-lg hover:border-pink-300
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 bg-pink-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <FileText size={20} className="text-pink-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">
              {historia.datos_empleado.nombre_completo || 'Sin nombre'}
            </h3>
            <p className="text-sm text-gray-500 truncate">
              {historia.datos_empleado.documento || 'Sin documento'} • {historia.tipo_emo?.toUpperCase() || 'N/A'}
            </p>
          </div>
        </div>

        <ChevronRight size={20} className="text-gray-400 flex-shrink-0" />
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Fecha */}
        <div className="flex items-center gap-2 text-sm">
          <Calendar size={14} className="text-gray-400 flex-shrink-0" />
          <span className="text-gray-600 truncate">
            {historia.fecha_emo ? format(new Date(historia.fecha_emo), 'dd MMM yyyy', { locale: es }) : 'Sin fecha'}
          </span>
        </div>

        {/* Cargo */}
        {historia.datos_empleado.cargo && (
          <div className="flex items-center gap-2 text-sm">
            <Briefcase size={14} className="text-gray-400 flex-shrink-0" />
            <span className="text-gray-600 truncate">
              {historia.datos_empleado.cargo}
            </span>
          </div>
        )}

        {/* Diagnósticos count */}
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">Diagnósticos:</span>
          <span className="font-medium text-gray-900">
            {historia.diagnosticos?.length || 0}
          </span>
        </div>

        {/* Confianza */}
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">Confianza:</span>
          <span className={`font-medium ${getConfidenceColor(historia.confianza_extraccion || 0)}`}>
            {Math.round((historia.confianza_extraccion || 0) * 100)}%
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        {/* Aptitud */}
        <Badge variant={aptitudBadge.variant} size="sm">
          {aptitudBadge.label}
        </Badge>

        {/* Alertas */}
        {alertasAltas > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-red-600">
            <AlertCircle size={14} />
            <span>{alertasAltas} alerta{alertasAltas > 1 ? 's' : ''} alta{alertasAltas > 1 ? 's' : ''}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultCard;
