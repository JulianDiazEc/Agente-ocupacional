import React, { ReactNode } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Footer } from './Footer';

interface MainLayoutProps {
  children?: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '7xl' | 'full';
  noPadding?: boolean;
}

/**
 * Layout principal de la aplicación
 * Incluye Header, contenido principal y Footer
 * Soporta tanto children como Outlet de React Router
 */
export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  className = '',
  maxWidth = '7xl',
  noPadding = false,
}) => {
  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '7xl': 'max-w-7xl',
    full: 'max-w-full',
  };

  const paddingClasses = noPadding ? '' : 'px-4 sm:px-6 lg:px-8 py-8';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <main className={`flex-1 ${className}`}>
        <div className={`${maxWidthClasses[maxWidth]} mx-auto ${paddingClasses}`}>
          {/* Usar children si se proporciona, sino usar Outlet para React Router */}
          {children || <Outlet />}
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default MainLayout;
