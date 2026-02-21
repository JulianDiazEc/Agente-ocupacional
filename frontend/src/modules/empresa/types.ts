export interface EmpresaBase {
  id: string;
  nombre: string;
  nit?: string;
  responsable_sst_nombre?: string;
  responsable_sst_email?: string;
  responsable_sst_telefono?: string;
  ges_count?: number;
  sve_count?: number;
}

export interface Ges {
  id: string;
  empresa_id: string;
  nombre: string;
  descripcion?: string;
  cargos?: string[];
  peligros_principales?: string[];
  examenes_incluidos?: string[];
  criterios_clinicos?: string;
  relacion_examenes?: string;
}

export type SveTipo =
  | 'visual'
  | 'auditivo'
  | 'quimico'
  | 'cardiovascular'
  | 'psicosocial'
  | 'osteomuscular'
  | 'btx';

export interface Sve {
  id: string;
  empresa_id: string;
  tipo?: SveTipo;
  nombre: string;
  descripcion?: string;
  objetivo?: string;
  estado?: string;
  activo?: boolean;
}

export interface EmpresaDetail extends EmpresaBase {
  ges: Ges[];
  sve: Sve[];
}

export interface CreateEmpresaInput {
  nombre: string;
  nit?: string;
  responsable_sst_nombre: string;
  responsable_sst_email: string;
  responsable_sst_telefono: string;
}

export type UpdateEmpresaInput = Partial<CreateEmpresaInput>;

export interface CreateGesInput {
  nombre: string;
  descripcion?: string;
  cargos: string[];
  peligros_principales: string[];
  examenes_incluidos?: string[];
  criterios_clinicos?: string;
  relacion_examenes?: string;
}

export interface CreateSveInput {
  tipo: SveTipo;
  descripcion?: string;
  objetivo?: string;
  estado?: string;
}
