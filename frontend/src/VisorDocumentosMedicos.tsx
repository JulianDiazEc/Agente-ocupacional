import React, { useState } from 'react';
import { 
  FileText, Download, Upload, CheckCircle, AlertCircle, X,
  Eye, FileCheck, Activity, Brain, ChevronLeft, FileWarning
} from 'lucide-react';

interface VacunaInfo {
  nombre: string;
  dosis?: string;
}

interface PersonInfo {
  document_id?: string;
  age?: number;
}

interface DocumentoResultado {
  exam_label: string;
  page_count: number;
  image_count: number;
}

interface ResumenClinico {
  persona?: string;
  exam_category?: string;
  person_info: PersonInfo;
  target_role?: string;
  company?: string;
  resumen_tecnico?: { [sistema: string]: string[] };
  nota_resumen?: string;
  vacunas?: VacunaInfo[];
  llm_applied: boolean;
  hallazgos_grouped?: { [sistema: string]: string[] };
}

interface FormData {
  persona: string;
  company: string;
  target_role: string;
  embed_images: boolean;
  files: File[];
}

const VisorDocumentosMedicos = () => {
  const [vista, setVista] = useState<'carga' | 'resultados'>('carga');
  const [formData, setFormData] = useState<FormData>({
    persona: '',
    company: '',
    target_role: '',
    embed_images: true,
    files: []
  });

  // Estado para resultados (mock data)
  const [procesando, setProcesando] = useState(false);
  const [mostrarBannerExito, setMostrarBannerExito] = useState(true);
  const [errores, setErrores] = useState<string[]>([]);
  
  const [resumenClinico, setResumenClinico] = useState<ResumenClinico>({
    persona: 'De acuerdo al examen médico realizado a la',
    exam_category: 'Examen Médico Ocupacional',
    person_info: {
      document_id: '36726430',
      age: 47
    },
    target_role: 'NA Cargo: AYUDANTE DE OBRA',
    company: 'POWERCHINA INTERNATIONAL GROUP LIMITED SUCURSAL COLOMBIA POWERCHINA INTERNATIONAL GROUP LIMITED SUCURSAL COLOMBIA',
    resumen_tecnico: {
      'General': ['Se emiten restricciones ocupacionales específicas.'],
      'Osteomuscular': ['Escoliosis'],
      'Visual': ['Astigmatismo documentado en el examen visual.']
    },
    nota_resumen: 'Evaluación ocupacional realizada. Se emiten restricciones ocupacionales específicas. Hallazgos relevantes: escoliosis en el sistema osteomuscular y astigmatismo documentado en el examen visual.',
    llm_applied: true,
    hallazgos_grouped: {
      'General': ['Se emiten restricciones ocupacionales específicas.'],
      'Osteomuscular': ['Escoliosis'],
      'Visual': ['Astigmatismo documentado en el examen visual.']
    }
  });

  const [documentosProcesados, setDocumentosProcesados] = useState<DocumentoResultado[]>([
    {
      exam_label: 'Examen Médico Ocupacional',
      page_count: 3,
      image_count: 2
    }
  ]);

  const [archivosGenerados] = useState({
    json: 'resultado_36726430.json',
    lineasLimpias: 'lineas_limpias_36726430.txt',
    hallazgos: 'hallazgos_36726430.json',
    resumen: 'resumen_36726430.json'
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFormData(prev => ({ ...prev, files: Array.from(e.target.files || []) }));
    }
  };

  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const procesarDocumentos = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.files.length === 0) {
      setErrores(['Por favor selecciona al menos un archivo PDF']);
      return;
    }

    setProcesando(true);
    
    // Simular procesamiento
    setTimeout(() => {
      setProcesando(false);
      setVista('resultados');
      setMostrarBannerExito(true);
    }, 2000);
  };

  const descargarArchivo = (filename: string) => {
    console.log(`Descargando: ${filename}`);
    alert(`Iniciando descarga de: ${filename}`);
  };

  const volverACarga = () => {
    setVista('carga');
    setFormData({
      persona: '',
      company: '',
      target_role: '',
      embed_images: true,
      files: []
    });
  };

  // Vista de Carga
  if (vista === 'carga') {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-pink-500 rounded-lg flex items-center justify-center">
                <FileText size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Visor de Documentos Médicos
                </h1>
                <p className="text-sm text-gray-500">
                  Procesamiento inteligente con Azure Document Intelligence
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {errores.length > 0 && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="text-red-500 mt-0.5" size={20} />
                <div className="flex-1">
                  <h4 className="font-medium text-red-800 mb-2">Errores encontrados</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {errores.map((error, idx) => (
                      <li key={idx} className="text-red-700 text-sm">{error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-6">
              <p className="text-gray-600 mb-6">
                Carga uno o varios PDFs para extraer su contenido usando Azure Document Intelligence.
              </p>

              <form onSubmit={procesarDocumentos}>
                {/* Identificador de persona */}
                <div className="mb-6">
                  <label htmlFor="persona" className="block text-sm font-medium text-gray-700 mb-2">
                    Identificador de la persona (opcional)
                  </label>
                  <input
                    type="text"
                    id="persona"
                    value={formData.persona}
                    onChange={(e) => handleInputChange('persona', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm 
                             focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                    placeholder="Ej. CC12345 o nombre completo"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Se utilizará para nombrar el archivo JSON consolidado.
                  </p>
                </div>

                {/* Empresa y Cargo */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-2">
                      Empresa (opcional)
                    </label>
                    <input
                      type="text"
                      id="company"
                      value={formData.company}
                      onChange={(e) => handleInputChange('company', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm 
                               focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                      placeholder="Ej. ENFRAGEN TERMOVALLE S.A.S"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Si la historia no trae la empresa explícita, ingrésala aquí.
                    </p>
                  </div>

                  <div>
                    <label htmlFor="target_role" className="block text-sm font-medium text-gray-700 mb-2">
                      Cargo / Rol (opcional)
                    </label>
                    <input
                      type="text"
                      id="target_role"
                      value={formData.target_role}
                      onChange={(e) => handleInputChange('target_role', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm 
                               focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                      placeholder="Ej. Oficial de obra"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Sirve para validar el profesiograma asociado a la persona.
                    </p>
                  </div>
                </div>

                {/* Selector de archivos */}
                <div className="mb-6">
                  <label htmlFor="documents" className="block text-sm font-medium text-gray-700 mb-2">
                    Selecciona archivos PDF
                  </label>
                  <input
                    type="file"
                    id="documents"
                    accept=".pdf"
                    multiple
                    onChange={handleFileChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm 
                             focus:ring-2 focus:ring-pink-500 focus:border-transparent
                             file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0
                             file:text-sm file:font-medium file:bg-pink-50 file:text-pink-700
                             hover:file:bg-pink-100 cursor-pointer"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Puedes seleccionar varios archivos a la vez.
                  </p>
                  {formData.files.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {formData.files.map((file, idx) => (
                        <div key={idx} className="flex items-center space-x-2 text-sm text-gray-600">
                          <FileCheck size={14} className="text-green-500" />
                          <span>{file.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Checkbox imágenes */}
                <div className="mb-6">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.embed_images}
                      onChange={(e) => handleInputChange('embed_images', e.target.checked)}
                      className="rounded border-gray-300 text-pink-600 focus:ring-pink-500"
                    />
                    <span className="text-sm text-gray-700">
                      Incluir imágenes embebidas en el resultado (codificadas en base64).
                    </span>
                  </label>
                </div>

                {/* Botón submit */}
                <button
                  type="submit"
                  disabled={procesando}
                  className="w-full md:w-auto px-6 py-2.5 bg-pink-500 text-white rounded-lg 
                           hover:bg-pink-600 font-medium disabled:opacity-50 disabled:cursor-not-allowed
                           flex items-center justify-center space-x-2"
                >
                  {procesando ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Procesando...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      <span>Procesar documentos</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Vista de Resultados
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-pink-500 rounded-lg flex items-center justify-center">
              <FileText size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Visor de Documentos Médicos
              </h1>
              <p className="text-sm text-gray-500">
                Resultados del procesamiento
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navegación y contador */}
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={volverACarga}
            className="text-pink-600 hover:text-pink-700 font-medium flex items-center space-x-1"
          >
            <ChevronLeft size={16} />
            <span>Cargar nuevos documentos</span>
          </button>
          <span className="text-gray-500 text-sm">
            {documentosProcesados.length} documento(s) procesado(s)
          </span>
        </div>

        {/* Avisos/Errores */}
        {errores.length > 0 && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <FileWarning className="text-yellow-500 mt-0.5" size={20} />
              <div className="flex-1">
                <h4 className="font-medium text-yellow-800 mb-2">Avisos</h4>
                <ul className="list-disc list-inside space-y-1">
                  {errores.map((error, idx) => (
                    <li key={idx} className="text-yellow-700 text-sm">{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Banner de éxito */}
        {mostrarBannerExito && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <CheckCircle className="text-green-500 mt-0.5" size={20} />
                <div className="flex-1">
                  <h4 className="font-medium text-green-800 mb-2">Procesado correctamente</h4>
                  <p className="text-green-700 text-sm mb-3">
                    Descarga los archivos generados para compartirlos con otros agentes:
                  </p>
                  <ul className="space-y-2">
                    <ArchivoDescargable
                      nombre="JSON agrupado"
                      descripcion="(salida directa de Azure Document Intelligence)"
                      filename={archivosGenerados.json}
                      onDescargar={descargarArchivo}
                    />
                    <ArchivoDescargable
                      nombre="Líneas limpias"
                      descripcion="(texto normalizado por examen)"
                      filename={archivosGenerados.lineasLimpias}
                      onDescargar={descargarArchivo}
                    />
                    <ArchivoDescargable
                      nombre="Hallazgos estructurados"
                      filename={archivosGenerados.hallazgos}
                      onDescargar={descargarArchivo}
                    />
                    <ArchivoDescargable
                      nombre="Resumen clínico"
                      filename={archivosGenerados.resumen}
                      onDescargar={descargarArchivo}
                    />
                  </ul>
                </div>
              </div>
              <button
                onClick={() => setMostrarBannerExito(false)}
                className="text-green-600 hover:text-green-700 ml-4"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        )}

        {/* Resumen Clínico */}
        {resumenClinico && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">Resumen clínico</h2>
              <button
                onClick={() => descargarArchivo(archivosGenerados.resumen)}
                className="px-4 py-2 text-pink-600 border border-pink-200 rounded-lg 
                         hover:bg-pink-50 font-medium flex items-center space-x-2"
              >
                <Download size={16} />
                <span>Descargar resumen</span>
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Información del paciente */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {resumenClinico.persona && (
                  <InfoCard label="Paciente" value={resumenClinico.persona} />
                )}
                {resumenClinico.person_info.document_id && (
                  <InfoCard label="Documento" value={resumenClinico.person_info.document_id} />
                )}
                {resumenClinico.person_info.age && (
                  <InfoCard label="Edad" value={resumenClinico.person_info.age.toString()} />
                )}
                {resumenClinico.target_role && (
                  <InfoCard label="Cargo objetivo" value={resumenClinico.target_role} />
                )}
                {resumenClinico.company && (
                  <InfoCard 
                    label="Empresa" 
                    value={resumenClinico.company}
                    className="md:col-span-2"
                  />
                )}
              </div>

              {/* Hallazgos por sistema */}
              {resumenClinico.resumen_tecnico && Object.keys(resumenClinico.resumen_tecnico).length > 0 && (
                <div className="space-y-4">
                  {Object.entries(resumenClinico.resumen_tecnico).map(([sistema, hallazgos]) => (
                    <SeccionHallazgos
                      key={sistema}
                      titulo={sistema}
                      items={hallazgos}
                    />
                  ))}
                </div>
              )}

              {/* Nota del agente */}
              {resumenClinico.nota_resumen && (
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-2">Nota del agente</h4>
                  <p className="text-gray-700 text-sm leading-relaxed">
                    {resumenClinico.nota_resumen}
                  </p>
                </div>
              )}

              {/* Vacunación */}
              {resumenClinico.vacunas && resumenClinico.vacunas.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Vacunación</h4>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    {resumenClinico.vacunas.map((vacuna, idx) => (
                      <li key={idx} className="text-gray-700">
                        {vacuna.nombre}
                        {vacuna.dosis && <span className="text-gray-500"> ({vacuna.dosis})</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Badge LLM */}
              <div className="flex items-center space-x-2">
                {resumenClinico.llm_applied ? (
                  <span className="inline-flex items-center space-x-2 bg-green-500 text-white 
                                 px-3 py-1.5 rounded-full text-xs font-medium">
                    <Brain size={14} />
                    <span>LLM aplicado</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-2 bg-yellow-500 text-white 
                                 px-3 py-1.5 rounded-full text-xs font-medium">
                    <AlertCircle size={14} />
                    <span>LLM no disponible</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Hallazgos Detectados */}
        {resumenClinico?.hallazgos_grouped && Object.keys(resumenClinico.hallazgos_grouped).length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Hallazgos detectados</h2>
            </div>

            <div className="p-6 space-y-4">
              {Object.entries(resumenClinico.hallazgos_grouped).map(([sistema, hallazgos]) => (
                <div key={sistema}>
                  <h4 className="font-semibold text-gray-900 mb-2">{sistema}</h4>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    {hallazgos.map((hallazgo, idx) => (
                      <li key={idx} className="text-gray-700">{hallazgo}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Archivos Procesados */}
        {documentosProcesados.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Archivos procesados</h3>
            </div>
            <ul className="divide-y divide-gray-200">
              {documentosProcesados.map((doc, idx) => (
                <li key={idx} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                  <div>
                    <p className="font-medium text-gray-900">{doc.exam_label}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {doc.page_count} páginas · {doc.image_count} imágenes detectadas
                    </p>
                  </div>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs 
                                 font-medium bg-green-100 text-green-800">
                    Listo
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// Componentes auxiliares
const ArchivoDescargable: React.FC<{
  nombre: string;
  descripcion?: string;
  filename: string;
  onDescargar: (filename: string) => void;
}> = ({ nombre, descripcion, filename, onDescargar }) => (
  <li className="flex items-center space-x-2">
    <button
      onClick={() => onDescargar(filename)}
      className="text-pink-600 hover:text-pink-700 font-medium hover:underline"
    >
      {nombre}
    </button>
    {descripcion && (
      <span className="text-green-700 text-xs">{descripcion}</span>
    )}
  </li>
);

const InfoCard: React.FC<{
  label: string;
  value: string;
  className?: string;
}> = ({ label, value, className = '' }) => (
  <div className={className}>
    <p className="text-sm font-medium text-gray-500 mb-1">{label}:</p>
    <p className="text-gray-900">{value}</p>
  </div>
);

const SeccionHallazgos: React.FC<{
  titulo: string;
  items: string[];
}> = ({ titulo, items }) => (
  <div>
    <h4 className="font-semibold text-gray-900 mb-2">{titulo}</h4>
    <ul className="list-disc list-inside space-y-1 ml-2">
      {items.map((item, idx) => (
        <li key={idx} className="text-gray-700">{item}</li>
      ))}
    </ul>
  </div>
);

export default VisorDocumentosMedicos;
