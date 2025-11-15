import React from 'react';
import { Heart } from 'lucide-react';

interface FooterProps {
  className?: string;
}

/**
 * Footer de la aplicación
 * Información de copyright y links
 */
export const Footer: React.FC<FooterProps> = ({ className = '' }) => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={`bg-white border-t border-gray-200 mt-auto ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Copyright */}
          <div className="text-sm text-gray-600 text-center md:text-left">
            <p className="flex items-center gap-2 justify-center md:justify-start">
              © {currentYear} Narah Metrics. Todos los derechos reservados.
            </p>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6 text-sm">
            <a
              href="#"
              className="text-gray-600 hover:text-pink-600 transition-colors"
            >
              Documentación
            </a>
            <a
              href="#"
              className="text-gray-600 hover:text-pink-600 transition-colors"
            >
              Soporte
            </a>
            <a
              href="#"
              className="text-gray-600 hover:text-pink-600 transition-colors"
            >
              Privacidad
            </a>
          </div>

          {/* Credits */}
          <div className="text-sm text-gray-500 flex items-center gap-1">
            <span>Hecho con</span>
            <Heart size={14} className="text-pink-500 fill-pink-500" />
            <span>por Narah Metrics</span>
          </div>
        </div>

        {/* Tech Stack Info */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center">
            Azure Document Intelligence • Claude Sonnet 4 • React + TypeScript • Material UI
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
