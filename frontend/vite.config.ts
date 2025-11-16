import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Plugin personalizado para eliminar funciones color(display-p3) del CSS
function removeP3ColorsPlugin() {
  return {
    name: 'remove-p3-colors',
    enforce: 'post' as const,
    generateBundle(_options: any, bundle: any) {
      for (const fileName in bundle) {
        const file = bundle[fileName];
        if (fileName.endsWith('.css') && file.type === 'asset') {
          let css = file.source as string;

          // Eliminar bloques @supports con color(display-p3)
          // Buscar el índice de inicio
          const pattern = /@supports\s*\(color:\s*color\(display-p3/g;
          let match;

          while ((match = pattern.exec(css)) !== null) {
            const startIndex = match.index;
            let braceCount = 0;
            let endIndex = startIndex;

            // Encontrar la llave de apertura del @supports
            for (let i = startIndex; i < css.length; i++) {
              if (css[i] === '{') {
                braceCount = 1;
                endIndex = i + 1;
                break;
              }
            }

            // Encontrar la llave de cierre correspondiente
            for (let i = endIndex; i < css.length && braceCount > 0; i++) {
              if (css[i] === '{') braceCount++;
              if (css[i] === '}') braceCount--;
              if (braceCount === 0) {
                endIndex = i + 1;
                break;
              }
            }

            // Eliminar el bloque
            css = css.substring(0, startIndex) + css.substring(endIndex);
            pattern.lastIndex = startIndex;
          }

          file.source = css;
        }
      }
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), removeP3ColorsPlugin()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@services': path.resolve(__dirname, './src/services'),
      '@types': path.resolve(__dirname, './src/types'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@contexts': path.resolve(__dirname, './src/contexts'),
      '@theme': path.resolve(__dirname, './src/theme'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
