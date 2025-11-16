import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Función para convertir OKLCH a RGB (aproximación simplificada)
function oklchToRgb(l: number, c: number, h: number): string {
  // Conversión simplificada: OKLCH → sRGB
  // Para producción, esto es suficiente para colores web básicos

  // Convertir lightness (0-100 → 0-1)
  const L = l / 100;

  // Convertir hue a radianes
  const hRad = (h * Math.PI) / 180;

  // Convertir a coordenadas a/b
  const a = c * Math.cos(hRad);
  const b = c * Math.sin(hRad);

  // OKLAB → Linear RGB (matriz simplificada)
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.2914855480 * b;

  const l3 = l_ * l_ * l_;
  const m3 = m_ * m_ * m_;
  const s3 = s_ * s_ * s_;

  let r = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3;
  let g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3;
  let bVal = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3;

  // Gamma correction (linear → sRGB)
  const gammaCorrect = (val: number) => {
    if (val <= 0.0031308) return 12.92 * val;
    return 1.055 * Math.pow(val, 1 / 2.4) - 0.055;
  };

  r = gammaCorrect(r);
  g = gammaCorrect(g);
  bVal = gammaCorrect(bVal);

  // Clamp y convertir a 0-255
  const clamp = (val: number) => Math.max(0, Math.min(255, Math.round(val * 255)));

  return `rgb(${clamp(r)}, ${clamp(g)}, ${clamp(bVal)})`;
}

// Plugin personalizado para eliminar funciones de color modernas del CSS
function removeModernColorsPlugin() {
  return {
    name: 'remove-modern-colors',
    enforce: 'post' as const,
    generateBundle(_options: any, bundle: any) {
      for (const fileName in bundle) {
        const file = bundle[fileName];
        if (fileName.endsWith('.css') && file.type === 'asset') {
          let css = file.source as string;

          // 1. Convertir oklch() a rgb()
          css = css.replace(/oklch\(([\d.]+)%\s+([\d.]+)\s+([\d.]+)\)/g, (match, l, c, h) => {
            return oklchToRgb(parseFloat(l), parseFloat(c), parseFloat(h));
          });

          // 2. Eliminar bloques @supports con color-mix
          const colorMixPattern = /@supports\s*\([^)]*color-mix\(/g;
          let match;

          while ((match = colorMixPattern.exec(css)) !== null) {
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
            colorMixPattern.lastIndex = startIndex;
          }

          // 3. Reemplazar "in oklab" con "in srgb" en gradientes
          css = css.replace(/in oklab/g, 'in srgb');

          file.source = css;
        }
      }
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), removeModernColorsPlugin()],
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
