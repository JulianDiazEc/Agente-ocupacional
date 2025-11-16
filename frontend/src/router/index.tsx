/**
 * Configuración de rutas con React Router
 */

import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import {
  HomePage,
  UploadPage,
  ResultsListPage,
  ResultDetailPage,
  StatsPage,
} from '@/pages';

/**
 * Definición de rutas
 */
const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <MainLayout />,
      children: [
        {
          index: true,
          element: <HomePage />,
        },
        {
          path: 'upload',
          element: <UploadPage />,
        },
        {
          path: 'results',
          element: <ResultsListPage />,
        },
        {
          path: 'results/:id',
          element: <ResultDetailPage />,
        },
        {
          path: 'stats',
          element: <StatsPage />,
        },
        {
          path: '*',
          element: <Navigate to="/" replace />,
        },
      ],
    },
  ],
  {
    future: {
      v7_startTransition: true,
    },
  }
);

/**
 * Componente AppRouter
 */
export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;
