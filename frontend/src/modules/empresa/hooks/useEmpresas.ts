import { useCallback, useEffect, useState } from 'react';
import { empresaApi } from '../services/empresaApi';
import { EmpresaBase } from '../types';

interface State {
  data: EmpresaBase[];
  loading: boolean;
  error: string | null;
}

export const useEmpresas = () => {
  const [state, setState] = useState<State>({
    data: [],
    loading: true,
    error: null,
  });

  const fetchEmpresas = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await empresaApi.getEmpresas();
      setState({ data, loading: false, error: null });
    } catch (error: any) {
      setState({
        data: [],
        loading: false,
        error: error?.response?.data?.error || 'No se pudieron cargar las empresas',
      });
    }
  }, []);

  useEffect(() => {
    fetchEmpresas();
  }, [fetchEmpresas]);

  return {
    ...state,
    refetch: fetchEmpresas,
  };
};
