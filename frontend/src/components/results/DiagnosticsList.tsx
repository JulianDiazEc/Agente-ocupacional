import React from 'react';
import { Activity, AlertCircle, CheckCircle } from 'lucide-react';
import { Badge } from '@/components/common';
import { Diagnostico } from '@/types';

interface DiagnosticsListProps {
  diagnosticos: Diagnostico[];
  className?: string;
}

/**
 * Tabla/Lista de diagnósticos CIE-10
 * Muestra código, descripción, tipo y si está relacionado con trabajo
 */
export const DiagnosticsList: React.FC<DiagnosticsListProps> = ({
  diagnosticos,
  className = '',
}) => {
  if (diagnosticos.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <Activity size={48} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500">No se registraron diagnósticos</p>
      </div>
    );
  }

  const getTipoBadge = (tipo: string) => {
    switch (tipo) {
      case 'principal':
        return { variant: 'error' as const, label: 'Principal' };
      case 'secundario':
        return { variant: 'warning' as const, label: 'Secundario' };
      case 'relacionado':
        return { variant: 'info' as const, label: 'Relacionado' };
      default:
        return { variant: 'default' as const, label: tipo };
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-50';
    if (confidence >= 0.7) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
              CIE-10
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
              Descripción
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">
              Tipo
            </th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wide">
              Relacionado trabajo
            </th>
            <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wide">
              Confianza
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {diagnosticos.map((diagnostico, index) => {
            const tipoBadge = getTipoBadge(diagnostico.tipo);

            return (
              <tr key={index} className="hover:bg-gray-50 transition-colors">
                {/* CIE-10 */}
                <td className="px-4 py-3">
                  <code className="px-2 py-1 bg-gray-100 text-gray-900 rounded text-sm font-mono">
                    {diagnostico.codigo_cie10}
                  </code>
                </td>

                {/* Descripción */}
                <td className="px-4 py-3">
                  <p className="text-sm text-gray-900">
                    {diagnostico.descripcion}
                  </p>
                </td>

                {/* Tipo */}
                <td className="px-4 py-3">
                  <Badge variant={tipoBadge.variant} size="sm">
                    {tipoBadge.label}
                  </Badge>
                </td>

                {/* Relacionado trabajo */}
                <td className="px-4 py-3 text-center">
                  {diagnostico.relacionado_trabajo ? (
                    <CheckCircle size={18} className="inline-block text-green-500" />
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>

                {/* Confianza */}
                <td className="px-4 py-3 text-center">
                  <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(diagnostico.confianza)}`}>
                    {Math.round(diagnostico.confianza * 100)}%
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Leyenda */}
      <div className="mt-4 flex items-center gap-4 text-xs text-gray-500 px-4">
        <div className="flex items-center gap-1.5">
          <CheckCircle size={14} className="text-green-500" />
          <span>Relacionado con el trabajo</span>
        </div>
        <div className="flex items-center gap-1.5">
          <AlertCircle size={14} className="text-gray-400" />
          <span>Confianza: Verde ≥90%, Amarillo ≥70%, Rojo &lt;70%</span>
        </div>
      </div>
    </div>
  );
};

export default DiagnosticsList;
