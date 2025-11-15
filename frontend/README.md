# Narah HC Processor - Frontend

Frontend React + TypeScript + Material UI para el sistema de procesamiento de historias clínicas ocupacionales.

## 🚀 Inicio Rápido

### Instalación

```bash
cd frontend
npm install
```

### Configuración

1. Copiar archivo de variables de entorno:
```bash
cp .env.example .env
```

2. Editar `.env` con la URL del backend (por defecto: `http://localhost:5000/api`)

### Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en: `http://localhost:3000`

### Build para Producción

```bash
npm run build
```

Los archivos compilados estarán en `dist/`

## 📁 Estructura

```
src/
├── assets/          # Imágenes, iconos, etc
├── components/      # Componentes React
│   ├── common/      # Componentes reutilizables
│   ├── layout/      # Layout (Header, Footer)
│   ├── upload/      # Componentes de upload
│   ├── results/     # Visualización de resultados
│   ├── export/      # Exportación
│   └── alerts/      # Alertas
├── pages/           # Páginas/vistas
├── services/        # API calls (axios)
├── hooks/           # Custom hooks
├── utils/           # Funciones helper
├── types/           # TypeScript types
├── contexts/        # React Context
└── theme/           # Tema Material UI
```

## 🛠️ Tecnologías

- React 18
- TypeScript
- Vite
- Material UI v5
- React Router v6
- Axios
- React Hook Form + Zod
- Recharts

## 📝 Scripts Disponibles

- `npm run dev` - Servidor de desarrollo
- `npm run build` - Build de producción
- `npm run preview` - Preview del build
- `npm run lint` - Linter
- `npm run type-check` - Verificar tipos TypeScript
