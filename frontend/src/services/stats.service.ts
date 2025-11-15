/**
 * Servicio para estadísticas y análisis
 */

import api from './api';
import { StatisticsResponse } from '@/types';

/**
 * Servicio de estadísticas
 */
export const statsService = {
  /**
   * Obtener estadísticas generales
   */
  async getStatistics(): Promise<StatisticsResponse> {
    const response = await api.get<StatisticsResponse>('/stats');
    return response.data;
  },

  /**
   * Calcular estadísticas localmente desde resultados
   * Útil cuando el backend no está disponible
   */
  async calculateLocalStats(results: any[]): Promise<StatisticsResponse> {
    const total = results.length;

    // Confianza promedio
    const avgConfidence =
      results.reduce((sum, r) => sum + (r.confianza_extraccion || 0), 0) / total || 0;

    // Contar alertas por severidad
    const alertas = results.reduce(
      (acc, r) => {
        r.alertas_validacion?.forEach((alerta: any) => {
          if (alerta.severidad === 'alta') acc.alta++;
          if (alerta.severidad === 'media') acc.media++;
          if (alerta.severidad === 'baja') acc.baja++;
        });
        return acc;
      },
      { alta: 0, media: 0, baja: 0 }
    );

    // Diagnósticos más frecuentes
    const diagnosticosMap = new Map<string, { descripcion: string; count: number }>();

    results.forEach((r) => {
      r.diagnosticos?.forEach((d: any) => {
        const key = d.codigo_cie10;
        if (diagnosticosMap.has(key)) {
          diagnosticosMap.get(key)!.count++;
        } else {
          diagnosticosMap.set(key, {
            descripcion: d.descripcion,
            count: 1,
          });
        }
      });
    });

    const diagnosticos_frecuentes = Array.from(diagnosticosMap.entries())
      .map(([codigo, data]) => ({
        codigo,
        descripcion: data.descripcion,
        frecuencia: data.count,
      }))
      .sort((a, b) => b.frecuencia - a.frecuencia)
      .slice(0, 10);

    // Distribución por tipo EMO
    const distribucion_emo = results.reduce((acc, r) => {
      const tipo = r.tipo_emo;
      acc[tipo] = (acc[tipo] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total_procesados: total,
      confianza_promedio: Number(avgConfidence.toFixed(2)),
      alertas,
      diagnosticos_frecuentes,
      distribucion_emo,
    };
  },
};

export default statsService;
