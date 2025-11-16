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
    try {
      const response = await api.post(
        '/export/excel',
        { result_ids: resultIds },
        {
          responseType: 'blob',
        }
      );

      // Verificar que recibimos un blob válido
      if (!response.data || !(response.data instanceof Blob)) {
        throw new Error('La respuesta del servidor no es válida');
      }

      // Verificar que el blob no está vacío
      if (response.data.size === 0) {
        throw new Error('El archivo generado está vacío');
      }

      // Descargar archivo
      const filename = `historias_clinicas_${new Date().getTime()}.xlsx`;
      downloadFile(response.data, filename);
    } catch (error: any) {
      console.error('Error exportando a Excel:', error);

      // Si el error es un blob de error del backend, intentar leer el mensaje
      if (error.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text();
          const errorData = JSON.parse(text);
          throw new Error(errorData.detail || errorData.message || 'Error al exportar a Excel');
        } catch (parseError) {
          throw new Error('Error al exportar a Excel. Por favor intente nuevamente.');
        }
      }

      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Error al exportar a Excel. Por favor intente nuevamente.'
      );
    }
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
