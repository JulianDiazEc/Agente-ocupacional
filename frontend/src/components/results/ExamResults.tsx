import React from 'react';
import { Stethoscope, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { Badge } from '@/components/common';
import { ExamenParaclinico } from '@/types';

interface ExamResultsProps {
  examenes: ExamenParaclinico[];
  className?: string;
}

/**
 * Lista de resultados de exámenes paraclínicos
 * Muestra tipo, resultado, interpretación y hallazgos
 */
export const ExamResults: React.FC<ExamResultsProps> = ({
  examenes,
  className = '',
}) => {
  if (examenes.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <Stethoscope size={48} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500">No se registraron exámenes</p>
      </div>
    );
  }

  const getInterpretacionIcon = (interpretacion?: string) => {
    switch (interpretacion) {
      case 'normal':
        return <CheckCircle size={18} className="text-green-500" />;
      case 'anormal':
        return <XCircle size={18} className="text-red-500" />;
      case 'alterado':
        return <AlertTriangle size={18} className="text-yellow-500" />;
      default:
        return <AlertTriangle size={18} className="text-gray-400" />;
    }
  };

  const getInterpretacionBadge = (interpretacion?: string) => {
    switch (interpretacion) {
      case 'normal':
        return { variant: 'success' as const, label: 'Normal' };
      case 'anormal':
        return { variant: 'error' as const, label: 'Anormal' };
      case 'alterado':
        return { variant: 'warning' as const, label: 'Alterado' };
      default:
        return { variant: 'default' as const, label: 'Pendiente' };
    }
  };

  const getTipoLabel = (tipo: string) => {
    const labels: Record<string, string> = {
      laboratorio: 'Laboratorio',
      imagenologia: 'Imagenología',
      audiometria: 'Audiometría',
      visiometria: 'Visiometría',
      espirometria: 'Espirometría',
      electrocardiograma: 'Electrocardiograma',
      otro: 'Otro',
    };
    return labels[tipo] || tipo;
  };

  // Agrupar por tipo
  const groupedExams = examenes.reduce((acc, exam) => {
    const tipo = exam.tipo || 'otro';
    if (!acc[tipo]) {
      acc[tipo] = [];
    }
    acc[tipo].push(exam);
    return acc;
  }, {} as Record<string, ExamenParaclinico[]>);

  return (
    <div className={`space-y-6 ${className}`}>
      {Object.entries(groupedExams).map(([tipo, exams]) => (
        <div key={tipo}>
          {/* Tipo Header */}
          <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Stethoscope size={16} className="text-pink-500" />
            {getTipoLabel(tipo)}
            <span className="text-gray-500 font-normal">({exams.length})</span>
          </h4>

          {/* Exámenes */}
          <div className="space-y-3">
            {exams.map((examen, index) => {
              const interpretacionBadge = getInterpretacionBadge(examen.interpretacion);

              return (
                <div
                  key={index}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    {/* Nombre del examen */}
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900 mb-1">
                        {examen.nombre}
                      </h5>
                      {examen.fecha && (
                        <p className="text-xs text-gray-500">
                          Fecha: {new Date(examen.fecha).toLocaleDateString('es-CO')}
                        </p>
                      )}
                    </div>

                    {/* Interpretación */}
                    <div className="flex items-center gap-2">
                      {getInterpretacionIcon(examen.interpretacion)}
                      <Badge variant={interpretacionBadge.variant} size="sm">
                        {interpretacionBadge.label}
                      </Badge>
                    </div>
                  </div>

                  {/* Resultado y Valor */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                    {examen.resultado && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Resultado:</p>
                        <p className="text-sm text-gray-900">{examen.resultado}</p>
                      </div>
                    )}

                    {examen.valor && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Valor:</p>
                        <p className="text-sm text-gray-900">
                          {examen.valor} {examen.unidad || ''}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Hallazgos */}
                  {examen.hallazgos && (
                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <p className="text-xs text-gray-500 mb-1">Hallazgos:</p>
                      <p className="text-sm text-gray-700">{examen.hallazgos}</p>
                    </div>
                  )}

                  {/* Laboratorio */}
                  {examen.laboratorio && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500">
                        Laboratorio: <span className="text-gray-700">{examen.laboratorio}</span>
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ExamResults;
