import React, { useState } from 'react';
import { 
  FileText, Download, CheckCircle, AlertCircle, X,
  Eye, FileCheck, Activity, Brain, ChevronLeft, FileWarning,
  Stethoscope, Users, Droplet
} from 'lucide-react';

// Datos de ejemplo
const datosEjemplo = {
  documentosProcesados: [
    {
      exam_label: 'Examen Médico Ocupacional - Preingreso',
      page_count: 3,
      image_count: 2
    },
    {
      exam_label: 'Examen de Laboratorio Clínico',
      page_count: 2,
      image_count: 1
    }
  ],
  resumenClinico: {
    persona: 'De acuerdo al examen médico realizado a la',
    exam_category: 'Examen Médico Ocupacional',
    person_info: {
      document_id: '36726430',
      age: 47
    },
    target_role: 'NA Cargo: AYUDANTE DE OBRA',
    company: 'POWERCHINA INTERNATIONAL GROUP LIMITED SUCURSAL COLOMBIA',
    resumen_tecnico: {
      'General': ['Se emiten restricciones ocupacionales específicas.'],
      'Osteomuscular': ['Escoliosis'],
      'Visual': ['Astigmatismo documentado en el examen visual.'],
      'Cardiovascular': ['Presión arterial dentro de rangos normales']
    },
    nota_resumen: 'Evaluación ocupacional realizada. Se emiten restricciones ocupacionales específicas. Hallazgos relevantes: escoliosis en el sistema osteomuscular y astigmatismo documentado en el examen visual. Se recomienda seguimiento periódico y adaptaciones ergonómicas en el puesto de trabajo.',
    vacunas: [
      { nombre: 'Tétanos', dosis: 'Refuerzo' },
      { nombre: 'Hepatitis B', dosis: 'Esquema completo' },
      { nombre: 'Influenza', dosis: 'Anual 2024' }
    ],
    llm_applied: true,
    hallazgos_grouped: {
      'General': ['Se emiten restricciones ocupacionales específicas.'],
      'Osteomuscular': ['Escoliosis', 'Postura compensatoria'],
      'Visual': ['Astigmatismo documentado en el examen visual.', 'Agudeza visual corregida normal'],
      'Cardiovascular': ['Presión arterial 120/80 mmHg', 'Frecuencia cardíaca 72 lpm']
    }
  },
  archivosGenerados: {
    json: 'resultado_36726430.json',
    lineasLimpias: 'lineas_limpias_36726430.txt',
    hallazgos: 'hallazgos_36726430.json',
    resumen: 'resumen_36726430.json'
  },
  errores: []
};

const ResultadosVisorDocumentos = () => {
  const [mostrarBannerExito, setMostrarBannerExito] = useState(true);
  const [vista, setVista] = useState('resultados');

  const descargarArchivo = (filename) => {
    alert(`Descargando: ${filename}`);
  };

  const volverACarga = () => {
    alert('Regresando a la vista de carga de documentos...');
  };

  const { documentosProcesados, resumenClinico, archivosGenerados, errores } = datosEjemplo;

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
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4 shadow-sm">
            <div className="flex items-start space-x-3">
              <FileWarning className="text-yellow-500 mt-0.5 flex-shrink-0" size={20} />
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
          <div className="mb-6 bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <CheckCircle className="text-green-500 mt-0.5 flex-shrink-0" size={20} />
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 mb-2">Procesado correctamente</h4>
                  <p className="text-gray-600 text-sm mb-3">
                    Descarga los archivos generados para compartirlos con otros agentes:
                  </p>
                  <ul className="space-y-2">
                    <li className="flex items-start space-x-2">
                      <FileCheck className="text-green-500 flex-shrink-0 mt-0.5" size={14} />
                      <div className="flex-1">
                        <button
                          onClick={() => descargarArchivo(archivosGenerados.json)}
                          className="text-pink-600 hover:text-pink-700 font-medium hover:underline text-left"
                        >
                          JSON agrupado
                        </button>
                        <span className="text-gray-500 text-xs ml-2">
                          (salida directa de Azure Document Intelligence)
                        </span>
                      </div>
                    </li>
                    <li className="flex items-start space-x-2">
                      <FileCheck className="text-green-500 flex-shrink-0 mt-0.5" size={14} />
                      <div className="flex-1">
                        <button
                          onClick={() => descargarArchivo(archivosGenerados.lineasLimpias)}
                          className="text-pink-600 hover:text-pink-700 font-medium hover:underline text-left"
                        >
                          Líneas limpias
                        </button>
                        <span className="text-gray-500 text-xs ml-2">
                          (texto normalizado por examen)
                        </span>
                      </div>
                    </li>
                    <li className="flex items-start space-x-2">
                      <FileCheck className="text-green-500 flex-shrink-0 mt-0.5" size={14} />
                      <div className="flex-1">
                        <button
                          onClick={() => descargarArchivo(archivosGenerados.hallazgos)}
                          className="text-pink-600 hover:text-pink-700 font-medium hover:underline text-left"
                        >
                          Hallazgos estructurados
                        </button>
                      </div>
                    </li>
                    <li className="flex items-start space-x-2">
                      <FileCheck className="text-green-500 flex-shrink-0 mt-0.5" size={14} />
                      <div className="flex-1">
                        <button
                          onClick={() => descargarArchivo(archivosGenerados.resumen)}
                          className="text-pink-600 hover:text-pink-700 font-medium hover:underline text-left"
                        >
                          Resumen clínico
                        </button>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
              <button
                onClick={() => setMostrarBannerExito(false)}
                className="text-gray-400 hover:text-gray-600 ml-4 flex-shrink-0"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        )}

        {/* Resumen Clínico */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-pink-50 to-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-pink-100 rounded-lg flex items-center justify-center">
                  <FileText size={16} className="text-pink-600" />
                </div>
                <h2 className="text-xl font-bold text-gray-900">Resumen clínico</h2>
              </div>
              <button
                onClick={() => descargarArchivo(archivosGenerados.resumen)}
                className="px-4 py-2 text-pink-600 border border-pink-200 rounded-lg hover:bg-pink-50 font-medium flex items-center space-x-2"
              >
                <Download size={16} />
                <span>Descargar resumen</span>
              </button>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Grid de Información del paciente */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-100">
              <div>
                <div className="flex items-center space-x-1 mb-1">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Paciente</p>
                </div>
                <p className="text-sm text-gray-900 font-medium">{resumenClinico.persona}</p>
              </div>
              
              <div>
                <div className="flex items-center space-x-1 mb-1">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Tipo de examen</p>
                </div>
                <p className="text-sm text-gray-900 font-medium">{resumenClinico.exam_category}</p>
              </div>
              
              <div>
                <div className="flex items-center space-x-1 mb-1">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Documento</p>
                </div>
                <p className="text-sm text-gray-900 font-medium">{resumenClinico.person_info.document_id}</p>
              </div>
              
              <div>
                <div className="flex items-center space-x-1 mb-1">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Edad</p>
                </div>
                <p className="text-sm text-gray-900 font-medium">{resumenClinico.person_info.age} años</p>
              </div>
              
              <div className="lg:col-span-2">
                <div className="flex items-center space-x-1 mb-1">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Cargo objetivo</p>
                </div>
                <p className="text-sm text-gray-900 font-medium">{resumenClinico.target_role}</p>
              </div>
              
              <div className="md:col-span-2 lg:col-span-3">
                <div className="flex items-center space-x-1 mb-1">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Empresa</p>
                </div>
                <p className="text-sm text-gray-900 font-medium truncate">{resumenClinico.company}</p>
              </div>
            </div>

            {/* Hallazgos por sistema */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Hallazgos por Sistema
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(resumenClinico.resumen_tecnico).map(([sistema, hallazgos]) => (
                  <div key={sistema} className="bg-white rounded-lg p-4 border border-gray-200 hover:border-pink-200">
                    <h4 className="font-semibold text-gray-900 mb-3">
                      {sistema}
                    </h4>
                    <ul className="space-y-2">
                      {hallazgos.map((item, idx) => (
                        <li key={idx} className="flex items-start space-x-2 text-sm">
                          <div className="w-1.5 h-1.5 bg-pink-400 rounded-full mt-1.5 flex-shrink-0"></div>
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            {/* Nota del agente */}
            <div className="bg-pink-50 rounded-lg p-4 border border-pink-100">
              <h4 className="font-semibold text-gray-900 mb-2 flex items-center space-x-2">
                <Brain className="text-pink-500" size={18} />
                <span>Nota del agente</span>
              </h4>
              <p className="text-gray-700 text-sm leading-relaxed">
                {resumenClinico.nota_resumen}
              </p>
            </div>

            {/* Vacunación */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="font-semibold text-gray-900 mb-3">
                Vacunación
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {resumenClinico.vacunas.map((vacuna, idx) => (
                  <div key={idx} className="flex items-center space-x-2 text-sm">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full flex-shrink-0"></div>
                    <span className="text-gray-700">
                      {vacuna.nombre}
                      <span className="text-gray-500 ml-1">({vacuna.dosis})</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Badge LLM */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <span className="inline-flex items-center space-x-2 bg-green-500 text-white px-3 py-1.5 rounded-full text-xs font-medium shadow-sm">
                <Brain size={14} />
                <span>LLM aplicado</span>
              </span>
              <span className="text-xs text-gray-500">
                Procesado con Azure Document Intelligence
              </span>
            </div>
          </div>
        </div>

        {/* Hallazgos Detectados */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                <Stethoscope size={16} className="text-gray-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Hallazgos detectados</h2>
            </div>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(resumenClinico.hallazgos_grouped).map(([sistema, hallazgos]) => (
                <div key={sistema} className="bg-gray-50 rounded-lg p-4 border border-gray-100 hover:border-pink-200">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                    <div className="w-2 h-2 bg-pink-500 rounded-full"></div>
                    <span>{sistema}</span>
                  </h4>
                  <ul className="space-y-2">
                    {hallazgos.map((hallazgo, idx) => (
                      <li key={idx} className="flex items-start space-x-2 text-sm">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-1.5 flex-shrink-0"></div>
                        <span className="text-gray-700">{hallazgo}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Archivos Procesados */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                <FileCheck size={16} className="text-gray-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Archivos procesados</h3>
            </div>
          </div>
          <ul className="divide-y divide-gray-100">
            {documentosProcesados.map((doc, idx) => (
              <li key={idx} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 group">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center group-hover:bg-gray-200">
                    <FileText className="text-gray-600" size={18} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{doc.exam_label}</p>
                    <p className="text-sm text-gray-500 mt-1 flex items-center space-x-3">
                      <span className="flex items-center space-x-1">
                        <FileText size={12} />
                        <span>{doc.page_count} páginas</span>
                      </span>
                      <span className="text-gray-300">·</span>
                      <span className="flex items-center space-x-1">
                        <Eye size={12} />
                        <span>{doc.image_count} imágenes detectadas</span>
                      </span>
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 shadow-sm">
                  <CheckCircle size={12} className="mr-1" />
                  Listo
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Procesamiento completado • Azure Document Intelligence v3.1</p>
        </div>
      </div>
    </div>
  );
};

export default ResultadosVisorDocumentos;
