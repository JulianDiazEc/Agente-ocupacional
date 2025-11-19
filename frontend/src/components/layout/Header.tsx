import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText, Upload, BarChart3, Download, Building2 } from 'lucide-react';

interface HeaderProps {
  className?: string;
}

/**
 * Header principal de la aplicación
 * Incluye logo Narah, navegación y acciones
 */
export const Header: React.FC<HeaderProps> = ({ className = '' }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Inicio', icon: <FileText size={18} /> },
    { path: '/upload', label: 'Cargar', icon: <Upload size={18} /> },
    { path: '/results', label: 'Resultados', icon: <FileText size={18} /> },
    { path: '/stats', label: 'Estadísticas', icon: <BarChart3 size={18} /> },
    { path: '/admin/empresas', label: 'Empresas', icon: <Building2 size={18} /> },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <header className={`bg-white shadow-sm border-b border-gray-200 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo y Título */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-pink-500 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105">
              <FileText size={20} className="text-white" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold text-gray-900">
                Narah HC Processor
              </h1>
              <p className="text-xs text-gray-500">
                Historias Clínicas Ocupacionales
              </p>
            </div>
          </Link>

          {/* Navegación */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
                  ${
                    isActive(item.path)
                      ? 'bg-pink-50 text-pink-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Link
              to="/export"
              className="hidden sm:flex items-center gap-2 px-4 py-2 text-sm font-medium text-pink-600 hover:bg-pink-50 rounded-lg transition-colors"
            >
              <Download size={18} />
              <span>Exportar</span>
            </Link>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden border-t border-gray-200 py-3">
          <nav className="flex items-center justify-around">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex flex-col items-center gap-1 px-3 py-2 rounded-lg text-xs font-medium transition-all
                  ${
                    isActive(item.path)
                      ? 'text-pink-600'
                      : 'text-gray-600'
                  }
                `}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
