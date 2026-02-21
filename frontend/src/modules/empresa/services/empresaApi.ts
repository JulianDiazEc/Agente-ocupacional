import api from '@/services/api';
import {
  EmpresaBase,
  EmpresaDetail,
  CreateEmpresaInput,
  UpdateEmpresaInput,
  CreateGesInput,
  CreateSveInput,
  SveTipo,
} from '../types';

const buildUrl = (path = '') => `/empresas${path}`;

export const empresaApi = {
  async getEmpresas(): Promise<EmpresaBase[]> {
    const { data } = await api.get<EmpresaBase[]>(buildUrl());
    return data;
  },

  async getEmpresa(id: string): Promise<EmpresaDetail> {
    const { data } = await api.get<EmpresaDetail>(buildUrl(`/${id}`));
    return data;
  },

  async createEmpresa(payload: CreateEmpresaInput): Promise<EmpresaBase> {
    const { data } = await api.post<EmpresaBase>(buildUrl(), payload);
    return data;
  },

  async updateEmpresa(id: string, payload: UpdateEmpresaInput): Promise<EmpresaBase> {
    const { data } = await api.put<EmpresaBase>(buildUrl(`/${id}`), payload);
    return data;
  },

  async addGes(empresaId: string, payload: CreateGesInput) {
    const { data } = await api.post(buildUrl(`/${empresaId}/ges`), payload);
    return data;
  },

  async updateGes(empresaId: string, gesId: string, payload: CreateGesInput) {
    const { data } = await api.put(buildUrl(`/${empresaId}/ges/${gesId}`), payload);
    return data;
  },

  async addSve(empresaId: string, payload: CreateSveInput) {
    const { data } = await api.post(buildUrl(`/${empresaId}/sve`), payload);
    return data;
  },

  async setSve(empresaId: string, tipos: SveTipo[]) {
    const { data } = await api.put(buildUrl(`/${empresaId}/sve`), { tipos });
    return data;
  },
};
