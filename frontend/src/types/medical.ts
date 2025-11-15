/**
 * Tipos y interfaces para el sistema de historias clínicas
 * Basado en el schema de output_schema.json del backend
 */

// ============================================================================
// TIPOS BÁSICOS Y ENUMS
// ============================================================================

export type TipoDocumento = 'CC' | 'TI' | 'CE' | 'PA' | 'RC';

export type TipoEMO =
  | 'preingreso'
  | 'periodico'
  | 'postincapacidad'
  | 'retiro'
  | 'otro';

export type AptitudLaboral =
  | 'apto'
  | 'apto_con_restricciones'
  | 'no_apto_temporal'
  | 'no_apto_definitivo'
  | 'no_apto_permanente'
  | 'pendiente_concepto';

export interface AptitudLaboralDetalle {
  resultado_aptitud: AptitudLaboral;
  recomendaciones?: string;
  restricciones?: string;
}

export type AptitudLaboralData = AptitudLaboral | AptitudLaboralDetalle;

export type TipoDiagnostico = 'principal' | 'secundario' | 'relacionado';

export type InterpretacionExamen = 'normal' | 'anormal' | 'alterado' | 'pendiente';

export type TipoExamen =
  | 'laboratorio'
  | 'imagenologia'
  | 'audiometria'
  | 'visiometria'
  | 'espirometria'
  | 'electrocardiograma'
  | 'otro';

export type SeveridadAlerta = 'alta' | 'media' | 'baja';

export type ProgramaSVE =
  | 'dme'
  | 'psicosocial'
  | 'cardiovascular'
  | 'auditivo'
  | 'visual'
  | 'respiratorio'
  | 'osteomuscular'
  | 'otro';

// ============================================================================
// INTERFACES DE DATOS DEL EMPLEADO
// ============================================================================

export interface DatosEmpleado {
  nombre_completo: string;
  documento: string;
  tipo_documento: TipoDocumento;
  edad?: number;
  cargo?: string;
  empresa?: string;
  area?: string;
  confianza?: number;
}

// ============================================================================
// INTERFACES DE DIAGNÓSTICOS
// ============================================================================

export interface Diagnostico {
  codigo_cie10: string;
  descripcion: string;
  tipo: TipoDiagnostico;
  relacionado_trabajo: boolean;
  confianza: number;
}

// ============================================================================
// INTERFACES DE EXÁMENES
// ============================================================================

export interface Examen {
  tipo: TipoExamen;
  nombre: string;
  resultado?: string;
  valor?: string;
  unidad?: string;
  interpretacion: InterpretacionExamen;
  hallazgos?: string;
  confianza?: number;
}

export interface ExamenParaclinico extends Examen {
  fecha?: string;
  laboratorio?: string;
}

// ============================================================================
// INTERFACES DE ANTECEDENTES
// ============================================================================

export interface Antecedente {
  tipo: 'personal' | 'familiar' | 'laboral' | 'toxico_alergico';
  descripcion: string;
  fecha?: string;
  confianza?: number;
}

// ============================================================================
// INTERFACES DE RECOMENDACIONES
// ============================================================================

export interface Recomendacion {
  tipo: 'medica' | 'ocupacional' | 'seguimiento' | 'remision';
  descripcion: string;
  especialidad?: string;
  prioridad?: 'alta' | 'media' | 'baja';
  confianza?: number;
}

// ============================================================================
// INTERFACES DE ALERTAS
// ============================================================================

export interface AlertaValidacion {
  tipo?: string;
  severidad: SeveridadAlerta;
  campo?: string;
  campo_afectado?: string;
  mensaje?: string;
  descripcion?: string;
  accion_sugerida?: string;
}

// ============================================================================
// INTERFACES DE VACUNACIÓN
// ============================================================================

export interface Vacuna {
  nombre: string;
  dosis?: string;
  fecha?: string;
  lote?: string;
}

// ============================================================================
// INTERFAZ PRINCIPAL: HISTORIA CLÍNICA PROCESADA
// ============================================================================

export interface HistoriaClinicaProcesada {
  // Metadatos de procesamiento
  id_procesamiento: string;
  fecha_procesamiento: string;
  archivo_origen: string;

  // Datos del empleado
  datos_empleado: DatosEmpleado;

  // Datos del examen
  tipo_emo: TipoEMO;
  fecha_emo: string;
  medico_evaluador?: string;
  licencia_medica?: string;

  // Diagnósticos
  diagnosticos: Diagnostico[];

  // Exámenes
  examenes: ExamenParaclinico[];

  // Antecedentes
  antecedentes?: Antecedente[];

  // Aptitud laboral
  aptitud_laboral: AptitudLaboralData;
  restricciones_especificas?: string;
  recomendaciones_ocupacionales?: string[];

  // Recomendaciones y remisiones
  recomendaciones?: Recomendacion[];

  // Programas de vigilancia
  programas_sve: ProgramaSVE[];

  // Vacunación
  vacunas?: Vacuna[];

  // Métricas de calidad
  confianza_extraccion: number;
  tiempo_procesamiento?: number;

  // Validación
  alertas_validacion: AlertaValidacion[];

  // Datos adicionales
  observaciones?: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// INTERFAZ PARA CONSOLIDACIÓN DE MÚLTIPLES DOCUMENTOS
// ============================================================================

export interface HistoriaClinicaConsolidada extends HistoriaClinicaProcesada {
  // Documentos individuales que conforman la consolidación
  documentos_origen: string[];
  num_documentos_procesados: number;

  // Indica si hay duplicados detectados
  duplicados_eliminados?: {
    diagnosticos: number;
    examenes: number;
    recomendaciones: number;
  };
}

// ============================================================================
// INTERFACES PARA EL FORMULARIO DE UPLOAD
// ============================================================================

export interface FormDataUpload {
  persona?: string;
  company?: string;
  target_role?: string;
  embed_images: boolean;
  files: File[];
}

// ============================================================================
// INTERFACES PARA RESPUESTAS DEL API
// ============================================================================

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

export interface ProcessingResponse {
  result: HistoriaClinicaProcesada;
  processing_time: number;
  files_processed: number;
}

export interface ConsolidatedProcessingResponse {
  result: HistoriaClinicaConsolidada;
  processing_time: number;
  files_processed: number;
  person_id: string;
}

export interface StatisticsResponse {
  total_procesados: number;
  confianza_promedio: number;
  alertas: {
    alta: number;
    media: number;
    baja: number;
  };
  distribucion_emo: Record<string, number>;
  diagnosticos_frecuentes: Array<{
    codigo: string;
    descripcion: string;
    frecuencia: number;
  }>;
}

// ============================================================================
// INTERFACES PARA ESTADOS DE LA APLICACIÓN
// ============================================================================

export interface ProcessingState {
  isProcessing: boolean;
  progress: number;
  currentFile?: string;
  error?: string;
}

export interface UploadState {
  files: File[];
  formData: FormDataUpload;
  isValid: boolean;
}

export interface ResultsState {
  historias: HistoriaClinicaProcesada[];
  currentHistoria?: HistoriaClinicaProcesada;
  filters: ResultsFilters;
}

export interface ResultsFilters {
  searchTerm?: string;
  tipoEMO?: TipoEMO;
  aptitud?: AptitudLaboral;
  fechaInicio?: string;
  fechaFin?: string;
  conAlertasAltas?: boolean;
}

// ============================================================================
// INTERFACES PARA EXPORTACIÓN
// ============================================================================

export interface ExportOptions {
  format: 'excel' | 'json' | 'pdf';
  includeImages: boolean;
  resultIds: string[];
}

// ============================================================================
// TIPOS AUXILIARES
// ============================================================================

export type LoadingStatus = 'idle' | 'loading' | 'success' | 'error';

export interface Pagination {
  page: number;
  pageSize: number;
  total: number;
}
