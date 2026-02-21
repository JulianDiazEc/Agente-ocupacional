import { useCallback, useEffect, useState } from 'react';
import { empresaApi } from '../services/empresaApi';
import { EmpresaDetail, UpdateEmpresaInput } from '../types';

interface State {
  data: EmpresaDetail | null;
  loading: boolean;
  error: string | null;
  saving: boolean;
}

export const useEmpresa = (empresaId?: string) => {
  const [state, setState] = useState<State>({
    data: null,
    loading: true,
    error: null,
    saving: false,
  });

  const fetchEmpresa = useCallback(async () => {
    if (!empresaId) return;
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await empresaApi.getEmpresa(empresaId);
      setState((prev) => ({ ...prev, data, loading: false, error: null }));
    } catch (error: any) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error?.response?.data?.error || 'No se pudo cargar la empresa',
      }));
    }
  }, [empresaId]);

  useEffect(() => {
    fetchEmpresa();
  }, [fetchEmpresa]);

  const saveEmpresa = async (payload: UpdateEmpresaInput) => {
    if (!empresaId) return;
    setState((prev) => ({ ...prev, saving: true }));
    try {
      await empresaApi.updateEmpresa(empresaId, payload);
      await fetchEmpresa();
    } catch (error: any) {
      setState((prev) => ({
        ...prev,
        saving: false,
        error: error?.response?.data?.error || 'No se pudo guardar la empresa',
      }));
      throw error;
    } finally {
      setState((prev) => ({ ...prev, saving: false }));
    }
  };

  return {
    ...state,
    refetch: fetchEmpresa,
    saveEmpresa,
  };
};
