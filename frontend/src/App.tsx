/**
 * Componente principal de la aplicación
 * Integra providers, theme y router
 */

import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from '@/theme';
import { ProcessingProvider, ResultsProvider } from '@/contexts';
import { AppRouter } from '@/router';

/**
 * Componente App
 */
const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      {/* CssBaseline para reset de estilos de Material UI */}
      <CssBaseline />

      {/* Context Providers */}
      <ProcessingProvider>
        <ResultsProvider>
          {/* React Router */}
          <AppRouter />
        </ResultsProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
};

export default App;
