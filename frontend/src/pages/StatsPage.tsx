/**
 * Página de estadísticas
 * Muestra métricas y análisis de las historias procesadas
 */

import React, { useEffect, useState } from 'react';
import { BarChart3, RefreshCw, TrendingUp, AlertTriangle, FileText, Activity } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Alert } from '@/components/common/Alert';
import { useResults } from '@/contexts';
import { statsService } from '@/services';
import { StatisticsResponse } from '@/types';

/**
 * Componente StatsPage
 */
export const StatsPage: React.FC = () => {
  const { results } = useResults();
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Cargar estadísticas
   */
  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);

      // Intentar cargar desde el backend
      try {
        const data = await statsService.getStatistics();
        setStats(data);
      } catch (backendError) {
        // Si falla, calcular localmente
        console.warn('Backend stats no disponible, calculando localmente');
        const localStats = await statsService.calculateLocalStats(results);
        setStats(localStats);
      }
    } catch (err: any) {
      console.error('Error cargando estadísticas:', err);
      setError(err.message || 'Error al cargar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Cargar al montar
   */
  useEffect(() => {
    if (results.length > 0) {
      loadStats();
    }
  }, [results.length]);

  /**
   * Loading
   */
  if (loading) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Cargando estadísticas...</p>
      </div>
    );
  }

  /**
   * No hay datos
   */
  if (results.length === 0) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card variant="outlined">
          <div className="text-center py-12">
            <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">No hay estadísticas disponibles</h2>
            <p className="text-gray-600 mb-6">
              Procesa algunas historias clínicas para ver estadísticas y análisis
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Estadísticas y Análisis</h1>
          <p className="text-gray-600 mt-1">Métricas generales de historias procesadas</p>
        </div>
        <Button
          variant="outline"
          icon={<RefreshCw className={loading ? 'animate-spin' : ''} />}
          onClick={loadStats}
          disabled={loading}
        >
          Actualizar
        </Button>
      </div>

      {/* Error */}
      {error && (
        <Alert severity="media">
          <p className="font-medium">Error al cargar estadísticas</p>
          <p className="text-sm mt-1">{error}</p>
        </Alert>
      )}

      {stats && (
        <>
          {/* KPIs Principales */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Procesados */}
            <Card variant="elevated">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Procesados</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total_procesados}</p>
                </div>
                <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center">
                  <FileText className="w-6 h-6 text-pink-500" />
                </div>
              </div>
            </Card>

            {/* Confianza Promedio */}
            <Card variant="elevated">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Confianza Promedio</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.confianza_promedio}%</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
              </div>
              <div className="mt-2">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${
                      stats.confianza_promedio >= 90
                        ? 'bg-green-500'
                        : stats.confianza_promedio >= 70
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${stats.confianza_promedio}%` }}
                  />
                </div>
              </div>
            </Card>

            {/* Alertas Altas */}
            <Card variant="elevated">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Alertas Altas</p>
                  <p className="text-3xl font-bold text-red-600">{stats.alertas.alta}</p>
                </div>
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
              </div>
              <div className="mt-2 flex items-center gap-2 text-sm text-gray-600">
                <span className="text-yellow-600">{stats.alertas.media}</span> medias •
                <span className="text-blue-600">{stats.alertas.baja}</span> bajas
              </div>
            </Card>

            {/* Diagnósticos Únicos */}
            <Card variant="elevated">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Diagnósticos Únicos</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {stats.diagnosticos_frecuentes.length}
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Activity className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </Card>
          </div>

          {/* Distribución por Tipo EMO */}
          <Card
            title="Distribución por Tipo de EMO"
            icon={<BarChart3 className="w-5 h-5" />}
            variant="outlined"
          >
            <div className="space-y-3">
              {Object.entries(stats.distribucion_emo)
                .sort(([, a], [, b]) => b - a)
                .map(([tipo, count]) => {
                  const percentage = ((count / stats.total_procesados) * 100).toFixed(1);
                  return (
                    <div key={tipo}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700 capitalize">
                          {tipo.replace('_', ' ')}
                        </span>
                        <span className="text-sm text-gray-600">
                          {count} ({percentage}%)
                        </span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-pink-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </Card>

          {/* Diagnósticos Más Frecuentes */}
          <Card
            title="Diagnósticos Más Frecuentes"
            icon={<Activity className="w-5 h-5" />}
            variant="outlined"
          >
            {stats.diagnosticos_frecuentes.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        #
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Código CIE-10
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Descripción
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Frecuencia
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {stats.diagnosticos_frecuentes.map((diag, idx) => (
                      <tr key={diag.codigo} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-500">{idx + 1}</td>
                        <td className="px-4 py-3">
                          <Badge variant="info">{diag.codigo}</Badge>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">{diag.descripcion}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900">
                              {diag.frecuencia}
                            </span>
                            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden min-w-[60px]">
                              <div
                                className="h-full bg-pink-500"
                                style={{
                                  width: `${(diag.frecuencia / stats.total_procesados) * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center text-gray-500 py-6">No hay diagnósticos registrados</p>
            )}
          </Card>

          {/* Resumen de Alertas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card variant="outlined" className="border-red-200 bg-red-50">
              <div className="text-center">
                <AlertTriangle className="w-8 h-8 text-red-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-red-900">{stats.alertas.alta}</p>
                <p className="text-sm text-red-700">Alertas de Severidad Alta</p>
              </div>
            </Card>

            <Card variant="outlined" className="border-yellow-200 bg-yellow-50">
              <div className="text-center">
                <AlertTriangle className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-yellow-900">{stats.alertas.media}</p>
                <p className="text-sm text-yellow-700">Alertas de Severidad Media</p>
              </div>
            </Card>

            <Card variant="outlined" className="border-blue-200 bg-blue-50">
              <div className="text-center">
                <AlertTriangle className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                <p className="text-2xl font-bold text-blue-900">{stats.alertas.baja}</p>
                <p className="text-sm text-blue-700">Alertas de Severidad Baja</p>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
};

export default StatsPage;
