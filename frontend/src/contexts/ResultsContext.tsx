/**
 * Context para manejar resultados y búsquedas
 */

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { processingService } from '@/services';
import { HistoriaClinicaProcesada } from '@/types';

/**
 * Filtros de búsqueda
 */
export interface SearchFilters {
  searchTerm?: string;
  tipoEMO?: string;
  fechaInicio?: string;
  fechaFin?: string;
}

/**
 * Estado del contexto
 */
interface ResultsState {
  // Datos
  results: HistoriaClinicaProcesada[];
  filteredResults: HistoriaClinicaProcesada[];
  selectedResult: HistoriaClinicaProcesada | null;

  // Estado de carga
  loading: boolean;
  error: string | null;

  // Filtros
  filters: SearchFilters;

  // Acciones
  fetchResults: () => Promise<void>;
  fetchResultById: (id: string) => Promise<void>;
  searchResults: (filters: SearchFilters) => Promise<void>;
  setFilters: (filters: SearchFilters) => void;
  clearFilters: () => void;
  selectResult: (id: string | null) => void;
  refresh: () => Promise<void>;
}

const ResultsContext = createContext<ResultsState | undefined>(undefined);

/**
 * Props del provider
 */
interface ResultsProviderProps {
  children: ReactNode;
}

/**
 * Provider del contexto de resultados
 */
export const ResultsProvider: React.FC<ResultsProviderProps> = ({ children }) => {
  const [results, setResults] = useState<HistoriaClinicaProcesada[]>([]);
  const [filteredResults, setFilteredResults] = useState<HistoriaClinicaProcesada[]>([]);
  const [selectedResult, setSelectedResult] = useState<HistoriaClinicaProcesada | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFiltersState] = useState<SearchFilters>({});

  /**
   * Obtener todos los resultados
   */
  const fetchResults = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await processingService.getAllResults();
      setResults(data);
      setFilteredResults(data);
    } catch (err: any) {
      console.error('Error obteniendo resultados:', err);
      setError(err.response?.data?.error || err.message || 'Error al cargar los resultados');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Obtener un resultado específico por ID
   */
  const fetchResultById = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);

      const data = await processingService.getResultById(id);
      setSelectedResult(data);
    } catch (err: any) {
      console.error('Error obteniendo resultado:', err);
      setError(err.response?.data?.error || err.message || 'Error al cargar el resultado');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Buscar resultados con filtros
   */
  const searchResults = useCallback(
    async (searchFilters: SearchFilters) => {
      try {
        setLoading(true);
        setError(null);
        setFiltersState(searchFilters);

        const data = await processingService.searchResults(searchFilters);
        setFilteredResults(data);
      } catch (err: any) {
        console.error('Error buscando resultados:', err);
        setError(err.response?.data?.error || err.message || 'Error al buscar resultados');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /**
   * Establecer filtros (sin hacer búsqueda automática)
   */
  const setFilters = useCallback((newFilters: SearchFilters) => {
    setFiltersState(newFilters);
  }, []);

  /**
   * Limpiar filtros
   */
  const clearFilters = useCallback(() => {
    setFiltersState({});
    setFilteredResults(results);
  }, [results]);

  /**
   * Seleccionar un resultado
   */
  const selectResult = useCallback(
    (id: string | null) => {
      if (id === null) {
        setSelectedResult(null);
      } else {
        const result = results.find((r) => r.id_procesamiento === id);
        setSelectedResult(result || null);
      }
    },
    [results]
  );

  /**
   * Refrescar resultados
   */
  const refresh = useCallback(async () => {
    await fetchResults();
  }, [fetchResults]);

  /**
   * Cargar resultados al montar
   */
  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const value: ResultsState = {
    results,
    filteredResults,
    selectedResult,
    loading,
    error,
    filters,
    fetchResults,
    fetchResultById,
    searchResults,
    setFilters,
    clearFilters,
    selectResult,
    refresh,
  };

  return <ResultsContext.Provider value={value}>{children}</ResultsContext.Provider>;
};

/**
 * Hook para usar el contexto de resultados
 */
export const useResults = (): ResultsState => {
  const context = useContext(ResultsContext);
  if (context === undefined) {
    throw new Error('useResults must be used within a ResultsProvider');
  }
  return context;
};
