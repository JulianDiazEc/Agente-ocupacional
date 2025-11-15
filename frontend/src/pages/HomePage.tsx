/**
 * Página de inicio
 * Bienvenida y acceso rápido a funcionalidades
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Upload, BarChart3, Download, Shield, Zap } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useResults } from '@/contexts';

/**
 * Componente HomePage
 */
export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { results } = useResults();

  // Estadísticas rápidas
  const totalProcesados = results.length;
  const ultimosProcesados = results.slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-pink-100 rounded-full mb-4">
          <FileText className="w-8 h-8 text-pink-500" />
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Narah HC Processor
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Procesamiento inteligente de historias clínicas ocupacionales con IA
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card variant="elevated" hoverable>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-pink-100 rounded-full mb-3">
              <FileText className="w-6 h-6 text-pink-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{totalProcesados}</p>
            <p className="text-sm text-gray-600">Historias Procesadas</p>
          </div>
        </Card>

        <Card variant="elevated" hoverable onClick={() => navigate('/upload')}>
          <div className="text-center cursor-pointer">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-3">
              <Upload className="w-6 h-6 text-green-600" />
            </div>
            <p className="text-lg font-semibold text-gray-900">Cargar Nuevos</p>
            <p className="text-sm text-gray-600">Procesar documentos</p>
          </div>
        </Card>

        <Card variant="elevated" hoverable onClick={() => navigate('/stats')}>
          <div className="text-center cursor-pointer">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-3">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
            <p className="text-lg font-semibold text-gray-900">Estadísticas</p>
            <p className="text-sm text-gray-600">Ver análisis</p>
          </div>
        </Card>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card
          title="Características Principales"
          icon={<Zap className="w-5 h-5" />}
          variant="outlined"
        >
          <ul className="space-y-3">
            <li className="flex items-start">
              <Shield className="w-5 h-5 text-pink-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">Extracción Inteligente</p>
                <p className="text-sm text-gray-600">
                  Azure Document Intelligence + Claude 3.5 para precisión máxima
                </p>
              </div>
            </li>
            <li className="flex items-start">
              <FileText className="w-5 h-5 text-pink-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">Diagnósticos CIE-10</p>
                <p className="text-sm text-gray-600">
                  Identificación automática de códigos y descripciones
                </p>
              </div>
            </li>
            <li className="flex items-start">
              <Download className="w-5 h-5 text-pink-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">Exportación Multiple</p>
                <p className="text-sm text-gray-600">
                  Excel, JSON, formato Narah Metrics
                </p>
              </div>
            </li>
            <li className="flex items-start">
              <BarChart3 className="w-5 h-5 text-pink-500 mr-3 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">Análisis y Estadísticas</p>
                <p className="text-sm text-gray-600">
                  Dashboards con métricas clave y tendencias
                </p>
              </div>
            </li>
          </ul>
        </Card>

        {/* Recent Results */}
        <Card
          title="Últimos Procesados"
          icon={<FileText className="w-5 h-5" />}
          variant="outlined"
          action={
            totalProcesados > 0 ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/results')}
              >
                Ver todos
              </Button>
            ) : undefined
          }
        >
          {ultimosProcesados.length > 0 ? (
            <ul className="space-y-2">
              {ultimosProcesados.map((result) => (
                <li
                  key={result.id_procesamiento}
                  className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer"
                  onClick={() => navigate(`/results/${result.id_procesamiento}`)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {result.datos_empleado.nombre_completo}
                    </p>
                    <p className="text-xs text-gray-500">
                      {result.datos_empleado.documento} • {result.tipo_emo}
                    </p>
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(result.fecha_procesamiento).toLocaleDateString('es-ES', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 mb-4">No hay historias procesadas</p>
              <Button
                variant="primary"
                icon={<Upload />}
                onClick={() => navigate('/upload')}
              >
                Cargar Primera Historia
              </Button>
            </div>
          )}
        </Card>
      </div>

      {/* CTA Section */}
      <Card variant="filled" className="bg-gradient-to-r from-pink-500 to-pink-600">
        <div className="text-center py-8">
          <h2 className="text-2xl font-bold text-white mb-2">
            ¿Listo para empezar?
          </h2>
          <p className="text-pink-100 mb-6">
            Carga tus historias clínicas y obtén resultados en minutos
          </p>
          <Button
            variant="secondary"
            size="lg"
            icon={<Upload />}
            onClick={() => navigate('/upload')}
            className="bg-white text-pink-600 hover:bg-gray-50"
          >
            Cargar Documentos
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default HomePage;
