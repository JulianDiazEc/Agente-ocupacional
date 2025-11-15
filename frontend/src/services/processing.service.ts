/**
 * Servicio para procesamiento de historias clínicas
 * Integración con endpoints del backend Flask
 */

import api, { createFormData } from './api';
import {
  HistoriaClinicaProcesada,
  HistoriaClinicaConsolidada,
} from '@/types';

/**
 * Servicio de procesamiento
 */
export const processingService = {
  /**
   * Procesar un solo documento PDF
   */
  async processDocument(file: File): Promise<HistoriaClinicaProcesada> {
    const formData = createFormData({ file });

    const response = await api.post<HistoriaClinicaProcesada>(
      '/process',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  /**
   * Procesar múltiples documentos de una persona (consolidado)
   */
  async processPersonDocuments(
    files: File[],
    personId?: string
  ): Promise<HistoriaClinicaConsolidada> {
    const formData = createFormData({
      files,
      person_id: personId || 'consolidated',
    });

    const response = await api.post<HistoriaClinicaConsolidada>(
      '/process-person',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  /**
   * Obtener todos los resultados procesados
   */
  async getAllResults(): Promise<HistoriaClinicaProcesada[]> {
    const response = await api.get<HistoriaClinicaProcesada[]>('/results');
    return response.data;
  },

  /**
   * Obtener un resultado específico por ID
   */
  async getResultById(id: string): Promise<HistoriaClinicaProcesada> {
    const response = await api.get<HistoriaClinicaProcesada>(`/results/${id}`);
    return response.data;
  },

  /**
   * Buscar resultados con filtros
   * (implementar cuando el backend lo soporte)
   */
  async searchResults(filters: {
    searchTerm?: string;
    tipoEMO?: string;
    fechaInicio?: string;
    fechaFin?: string;
  }): Promise<HistoriaClinicaProcesada[]> {
    // Por ahora, filtrar localmente
    const allResults = await this.getAllResults();

    return allResults.filter((result) => {
      // Filtro por término de búsqueda
      if (filters.searchTerm) {
        const term = filters.searchTerm.toLowerCase();
        const matchesName = result.datos_empleado.nombre_completo
          .toLowerCase()
          .includes(term);
        const matchesDoc = result.datos_empleado.documento.includes(term);

        if (!matchesName && !matchesDoc) {
          return false;
        }
      }

      // Filtro por tipo EMO
      if (filters.tipoEMO && result.tipo_emo !== filters.tipoEMO) {
        return false;
      }

      // Filtro por fecha
      if (filters.fechaInicio || filters.fechaFin) {
        const fecha = new Date(result.fecha_emo);

        if (filters.fechaInicio && fecha < new Date(filters.fechaInicio)) {
          return false;
        }

        if (filters.fechaFin && fecha > new Date(filters.fechaFin)) {
          return false;
        }
      }

      return true;
    });
  },
};

export default processingService;
