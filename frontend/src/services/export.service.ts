/**
 * Servicio para exportación de resultados
 * Exportar a Excel, JSON, etc.
 */

import api, { downloadFile } from './api';

/**
 * Servicio de exportación
 */
export const exportService = {
  /**
   * Exportar resultados a Excel
   */
  async exportToExcel(resultIds?: string[]): Promise<void> {
    const response = await api.post(
      '/export/excel',
      { result_ids: resultIds },
      {
        responseType: 'blob',
      }
    );

    // Descargar archivo
    const filename = `historias_clinicas_${new Date().getTime()}.xlsx`;
    downloadFile(response.data, filename);
  },

  /**
   * Exportar a formato Narah Metrics
   */
  async exportToNarah(resultIds?: string[]): Promise<void> {
    const response = await api.post(
      '/export/narah',
      { result_ids: resultIds },
      {
        responseType: 'blob',
      }
    );

    // Descargar archivo
    const filename = `narah_import_${new Date().getTime()}.xlsx`;
    downloadFile(response.data, filename);
  },

  /**
   * Exportar un resultado individual a JSON
   */
  async exportToJSON(result: any): Promise<void> {
    const json = JSON.stringify(result, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const filename = `${result.datos_empleado.documento}_${new Date().getTime()}.json`;
    downloadFile(blob, filename);
  },

  /**
   * Exportar múltiples resultados a JSON
   */
  async exportMultipleToJSON(results: any[]): Promise<void> {
    const json = JSON.stringify(results, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const filename = `historias_clinicas_${new Date().getTime()}.json`;
    downloadFile(blob, filename);
  },
};

export default exportService;
