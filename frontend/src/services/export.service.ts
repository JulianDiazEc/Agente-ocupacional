/**
 * Servicio para exportación de resultados
 * Exportar a Excel, PDF, etc.
 */

import api, { downloadFile } from './api';
import html2pdf from 'html2pdf.js';

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
   * Exportar el contenido visible a PDF
   * @param element - Elemento HTML a exportar (puede ser un id de string o un HTMLElement)
   * @param filename - Nombre del archivo PDF
   */
  async exportToPDF(element: string | HTMLElement, filename?: string): Promise<void> {
    try {
      // Obtener el elemento
      const targetElement = typeof element === 'string'
        ? document.getElementById(element)
        : element;

      if (!targetElement) {
        throw new Error('Elemento no encontrado para exportar');
      }

      // Configuración de html2pdf
      const options = {
        margin: [10, 10, 10, 10] as [number, number, number, number],
        filename: filename || `historia_clinica_${new Date().getTime()}.pdf`,
        image: { type: 'jpeg' as const, quality: 0.95 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          logging: false,
          letterRendering: true
        },
        jsPDF: {
          unit: 'mm' as const,
          format: 'letter' as const,
          orientation: 'portrait' as const
        },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      };

      // Generar PDF
      await html2pdf().set(options).from(targetElement).save();
    } catch (error: any) {
      console.error('Error exportando a PDF:', error);
      throw new Error(
        error.message || 'Error al exportar a PDF. Por favor intente nuevamente.'
      );
    }
  },
};

export default exportService;
