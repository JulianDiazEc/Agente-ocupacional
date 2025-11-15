/**
 * Página de lista de resultados
 * Muestra todos los resultados procesados con búsqueda y filtros
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, RefreshCw, FileText, Download } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Alert } from '@/components/common/Alert';
import { ResultCard } from '@/components/results/ResultCard';
import { useResults } from '@/contexts';
import { exportService } from '@/services';

/**
 * Componente ResultsListPage
 */
export const ResultsListPage: React.FC = () => {
  const navigate = useNavigate();
  const { filteredResults, loading, error, searchResults, clearFilters, refresh, filters } =
    useResults();

  const [searchTerm, setSearchTerm] = useState(filters.searchTerm || '');
  const [tipoEMO, setTipoEMO] = useState(filters.tipoEMO || '');
  const [fechaInicio, setFechaInicio] = useState(filters.fechaInicio || '');
  const [fechaFin, setFechaFin] = useState(filters.fechaFin || '');
  const [showFilters, setShowFilters] = useState(false);

  /**
   * Aplicar búsqueda
   */
  const handleSearch = async () => {
    await searchResults({
      searchTerm: searchTerm || undefined,
      tipoEMO: tipoEMO || undefined,
      fechaInicio: fechaInicio || undefined,
      fechaFin: fechaFin || undefined,
    });
  };

  /**
   * Limpiar filtros
   */
  const handleClearFilters = () => {
    setSearchTerm('');
    setTipoEMO('');
    setFechaInicio('');
    setFechaFin('');
    clearFilters();
  };

  /**
   * Exportar todos los resultados
   */
  const handleExportAll = async () => {
    const ids = filteredResults.map((r) => r.id_procesamiento);
    await exportService.exportToExcel(ids);
  };

  /**
   * Navegar al detalle
   */
  const handleResultClick = (id: string) => {
    navigate(`/results/${id}`);
  };

  const hasActiveFilters = searchTerm || tipoEMO || fechaInicio || fechaFin;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Historias Clínicas</h1>
          <p className="text-gray-600 mt-1">
            {filteredResults.length} {filteredResults.length === 1 ? 'resultado' : 'resultados'}
            {hasActiveFilters && ' (filtrado)'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            icon={<RefreshCw className={loading ? 'animate-spin' : ''} />}
            onClick={refresh}
            disabled={loading}
          >
            Actualizar
          </Button>
          {filteredResults.length > 0 && (
            <Button variant="outline" icon={<Download />} onClick={handleExportAll}>
              Exportar Todos
            </Button>
          )}
        </div>
      </div>

      {/* Search Bar */}
      <Card variant="outlined">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Buscar por nombre o documento..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              icon={<Filter />}
              onClick={() => setShowFilters(!showFilters)}
            >
              Filtros
            </Button>
            <Button variant="primary" onClick={handleSearch} disabled={loading}>
              Buscar
            </Button>
          </div>
        </div>

        {/* Filtros avanzados */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="tipoEMO" className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo EMO
                </label>
                <select
                  id="tipoEMO"
                  value={tipoEMO}
                  onChange={(e) => setTipoEMO(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                >
                  <option value="">Todos</option>
                  <option value="preocupacional">Preocupacional</option>
                  <option value="periodico">Periódico</option>
                  <option value="postincapacidad">Postincapacidad</option>
                  <option value="retiro">Retiro</option>
                </select>
              </div>
              <div>
                <label htmlFor="fechaInicio" className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha Inicio
                </label>
                <input
                  type="date"
                  id="fechaInicio"
                  value={fechaInicio}
                  onChange={(e) => setFechaInicio(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="fechaFin" className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha Fin
                </label>
                <input
                  type="date"
                  id="fechaFin"
                  value={fechaFin}
                  onChange={(e) => setFechaFin(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                />
              </div>
            </div>
            {hasActiveFilters && (
              <div className="mt-3">
                <Button variant="ghost" size="sm" onClick={handleClearFilters}>
                  Limpiar filtros
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Error */}
      {error && (
        <Alert severity="alta" closeable>
          <p className="font-medium">Error al cargar resultados</p>
          <p className="text-sm mt-1">{error}</p>
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <RefreshCw className="w-8 h-8 text-pink-500 animate-spin mx-auto mb-3" />
          <p className="text-gray-600">Cargando resultados...</p>
        </div>
      )}

      {/* Results Grid */}
      {!loading && filteredResults.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredResults.map((result) => (
            <ResultCard
              key={result.id_procesamiento}
              historia={result}
              onClick={() => handleResultClick(result.id_procesamiento)}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredResults.length === 0 && (
        <Card variant="outlined">
          <div className="text-center py-12">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {hasActiveFilters ? 'No se encontraron resultados' : 'No hay historias procesadas'}
            </h3>
            <p className="text-gray-600 mb-6">
              {hasActiveFilters
                ? 'Intenta ajustar los filtros de búsqueda'
                : 'Comienza cargando tu primera historia clínica'}
            </p>
            {hasActiveFilters ? (
              <Button variant="outline" onClick={handleClearFilters}>
                Limpiar filtros
              </Button>
            ) : (
              <Button variant="primary" onClick={() => navigate('/upload')}>
                Cargar Historia
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ResultsListPage;
