

# 🏗️ Arquitectura Frontend - Narah HC Processor

Documento de arquitectura completa del sistema frontend.

---

## 📋 Tabla de Contenidos

1. [Stack Tecnológico](#stack-tecnológico)
2. [Estructura de Directorios](#estructura-de-directorios)
3. [Paleta de Colores](#paleta-de-colores)
4. [Componentes](#componentes)
5. [Páginas](#páginas)
6. [Flujo de Datos](#flujo-de-datos)
7. [Servicios API](#servicios-api)
8. [Estado Global](#estado-global)

---

## 🛠️ Stack Tecnológico

### Core
- **React 18** - Framework UI
- **TypeScript 5.3** - Type safety
- **Vite 5** - Build tool & dev server

### UI/Styling
- **Material UI v5** - Component library
- **Tailwind CSS** - Utility-first CSS (opcional, para customización)
- **Lucide React** - Icon library
- **@emotion** - CSS-in-JS (viene con MUI)

### Routing & Forms
- **React Router v6** - Client-side routing
- **React Hook Form** - Form management
- **Zod** - Schema validation

### Data Fetching & State
- **Axios** - HTTP client
- **React Context** - Global state
- **React Query** (opcional, futuro) - Server state management

### Utils
- **date-fns** - Date manipulation
- **recharts** - Charts & graphs

---

## 📁 Estructura de Directorios

```
frontend/src/
├── assets/              # Static assets
│   ├── images/         # Logos, illustrations
│   └── icons/          # Custom icons
│
├── components/          # Reusable components
│   ├── common/         # Generic components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── Alert.tsx
│   │   ├── Modal.tsx
│   │   ├── Table.tsx
│   │   ├── Tabs.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Progress.tsx
│   │   ├── Skeleton.tsx
│   │   └── EmptyState.tsx
│   │
│   ├── layout/         # Layout components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx (opcional)
│   │   ├── Footer.tsx
│   │   └── MainLayout.tsx
│   │
│   ├── upload/         # Upload-specific components
│   │   ├── FileDropzone.tsx
│   │   ├── FileList.tsx
│   │   ├── UploadProgress.tsx
│   │   └── UploadForm.tsx
│   │
│   ├── results/        # Results-specific components
│   │   ├── ResultCard.tsx
│   │   ├── ResultsList.tsx
│   │   ├── ResultDetail.tsx
│   │   ├── PatientInfo.tsx
│   │   ├── DiagnosticsList.tsx
│   │   ├── ExamResults.tsx
│   │   ├── RecommendationsList.tsx
│   │   ├── ConfidenceScore.tsx
│   │   └── SystemFindings.tsx
│   │
│   ├── alerts/         # Alerts & validation
│   │   ├── AlertBadge.tsx
│   │   ├── AlertsList.tsx
│   │   ├── AlertDetail.tsx
│   │   └── ValidationSummary.tsx
│   │
│   └── export/         # Export functionality
│       ├── ExportButton.tsx
│       ├── ExportOptions.tsx
│       └── ExportHistory.tsx
│
├── pages/              # Page components (routes)
│   ├── HomePage.tsx
│   ├── UploadPage.tsx
│   ├── ResultsListPage.tsx
│   ├── ResultDetailPage.tsx
│   ├── ExportPage.tsx
│   └── StatsPage.tsx
│
├── services/           # API services
│   ├── api.ts          # Axios instance & config
│   ├── processing.service.ts
│   ├── export.service.ts
│   └── stats.service.ts
│
├── hooks/              # Custom React hooks
│   ├── useProcessing.ts
│   ├── useResults.ts
│   ├── useExport.ts
│   ├── useDebounce.ts
│   └── useLocalStorage.ts
│
├── contexts/           # React Context providers
│   ├── ProcessingContext.tsx
│   ├── ResultsContext.tsx
│   └── ThemeContext.tsx (opcional)
│
├── utils/              # Helper functions
│   ├── formatters.ts   # Date, number, text formatters
│   ├── validators.ts   # Custom validators
│   ├── constants.ts    # App constants
│   └── helpers.ts      # Misc helpers
│
├── types/              # TypeScript definitions
│   ├── medical.ts      # Medical data types ✅
│   ├── components.ts   # Component prop types ✅
│   └── index.ts        # Barrel export ✅
│
├── theme/              # MUI theme config
│   └── index.ts        # Theme definition
│
├── App.tsx             # Root component
├── main.tsx            # Entry point
└── routes.tsx          # Route definitions
```

---

## 🎨 Paleta de Colores

### Colores Principales (Narah Metrics)

```typescript
const colors = {
  // Brand colors
  primary: {
    main: '#EC4899',    // pink-500
    light: '#F9A8D4',   // pink-300
    dark: '#BE185D',    // pink-700
    contrast: '#FFFFFF',
  },

  // Neutral colors
  neutral: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    500: '#6B7280',
    700: '#374151',
    900: '#111827',
  },

  // Semantic colors
  success: {
    main: '#22C55E',    // green-500
    light: '#86EFAC',   // green-300
    dark: '#15803D',    // green-700
  },

  warning: {
    main: '#EAB308',    // yellow-500
    light: '#FDE047',   // yellow-300
    dark: '#A16207',    // yellow-700
  },

  error: {
    main: '#EF4444',    // red-500
    light: '#FCA5A5',   // red-300
    dark: '#B91C1C',    // red-700
  },

  info: {
    main: '#3B82F6',    // blue-500
    light: '#93C5FD',   // blue-300
    dark: '#1E40AF',    // blue-700
  },
};
```

### Uso de Colores

- **Primary (Pink)**: Botones primarios, links, iconos principales, badges
- **Success (Green)**: Estados exitosos, confirmaciones, badges LLM
- **Warning (Yellow)**: Alertas medias, avisos
- **Error (Red)**: Alertas altas, errores, validaciones fallidas
- **Neutral**: Textos, borders, backgrounds

---

## 🧩 Componentes

### Jerarquía de Componentes

#### 1. **Common Components** (Reutilizables)

##### Button
```typescript
<Button variant="primary" size="md" icon={<Upload />}>
  Procesar documentos
</Button>

Variants: primary | secondary | outline | ghost | danger
Sizes: sm | md | lg
```

##### Card
```typescript
<Card
  title="Resumen clínico"
  icon={<FileText />}
  headerAction={<Button>Descargar</Button>}
>
  {children}
</Card>

Variants: default | elevated | outlined | filled
```

##### Badge
```typescript
<Badge variant="success" icon={<CheckCircle />}>
  Procesado
</Badge>

Variants: success | warning | error | info | default
```

##### Alert
```typescript
<Alert
  severity="alta"
  title="Alerta crítica"
  message="Presión arterial elevada"
  onClose={handleClose}
/>
```

#### 2. **Upload Components**

##### FileDropzone
- Drag & drop zone
- File validation
- Visual feedback
- File preview

##### UploadProgress
- Progress bar per file
- Overall progress
- Cancel functionality
- Error handling

#### 3. **Results Components**

##### ResultCard
- Tarjeta resumen de HC
- Datos clave del paciente
- Badges de estado
- Click para ver detalle

##### PatientInfo
- Grid de información
- Datos estructurados
- Responsive layout

##### DiagnosticsList
- Tabla de diagnósticos
- CIE-10 codes
- Badges relacionados con trabajo
- Confidence scores

##### ExamResults
- Lista de exámenes
- Resultados normales/anormales
- Interpretaciones
- Hallazgos destacados

#### 4. **Layout Components**

##### MainLayout
```typescript
<MainLayout>
  <Header />
  <main>{children}</main>
  <Footer />
</MainLayout>
```

##### Header
- Logo Narah
- Navegación
- Actions (export, etc)

---

## 📄 Páginas

### 1. HomePage (Dashboard)
**Ruta:** `/`

**Componentes:**
- StatsCards (total procesados, confianza promedio, alertas)
- RecentResults (últimas 5 HCs procesadas)
- QuickActions (upload, export)

### 2. UploadPage
**Ruta:** `/upload`

**Componentes:**
- UploadForm
  - FileDropzone
  - PersonIdInput
  - CompanyInput
  - RoleInput
  - EmbedImagesCheckbox
- UploadProgress (cuando está procesando)
- ProcessingBanner

**Estados:**
- idle: Form visible
- uploading: Progress visible
- success: Redirect to results
- error: Show error message

### 3. ResultsListPage
**Ruta:** `/results`

**Componentes:**
- SearchBar
- Filters (tipo EMO, aptitud, fecha, alertas)
- ResultsList
  - ResultCard[] (grid)
- Pagination
- EmptyState (si no hay resultados)

### 4. ResultDetailPage
**Ruta:** `/results/:id`

**Componentes:**
- Breadcrumbs
- PatientInfo
- Tabs:
  - Resumen: DiagnosticsList, ExamResults
  - Hallazgos: SystemFindings
  - Recomendaciones: RecommendationsList
  - Alertas: AlertsList
  - Archivos: FilesList
- ExportButton
- BackButton

### 5. ExportPage
**Ruta:** `/export`

**Componentes:**
- ExportOptions (format, includeImages)
- ResultsSelection (multiselect)
- ExportButton
- ExportHistory

### 6. StatsPage
**Ruta:** `/stats`

**Componentes:**
- GlobalStats
- Charts:
  - DiagnosticsChart (top 10)
  - EMOTypesChart (pie)
  - ConfidenceChart (histogram)
  - AlertsChart (bar)
- TimeRangeSelector

---

## 🔄 Flujo de Datos

### 1. Upload Flow

```
User selects files
  ↓
FileDropzone validates files
  ↓
UploadForm submits
  ↓
ProcessingContext.processFiles()
  ↓
API POST /api/process-person
  ↓
Backend processes (Azure + Claude)
  ↓
API returns HistoriaClinicaProcesada
  ↓
ResultsContext.addResult()
  ↓
Navigate to /results/:id
```

### 2. Results Flow

```
User opens ResultsListPage
  ↓
useResults hook fetches data
  ↓
API GET /api/results
  ↓
ResultsContext.setResults()
  ↓
ResultsList renders ResultCard[]
  ↓
User clicks ResultCard
  ↓
Navigate to /results/:id
  ↓
ResultDetailPage fetches detail
  ↓
API GET /api/results/:id
  ↓
Render tabs with data
```

### 3. Export Flow

```
User selects results
  ↓
ExportOptions selects format
  ↓
ExportButton clicked
  ↓
API POST /api/export/excel
  ↓
Backend generates file
  ↓
Browser downloads file
  ↓
ExportHistory updated
```

---

## 🌐 Servicios API

### API Client Configuration

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 300000, // 5 min (procesamiento largo)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if needed
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Global error handling
    return Promise.reject(error);
  }
);

export default api;
```

### Processing Service

```typescript
// services/processing.service.ts

export const processingService = {
  // Procesar un documento
  processDocument(file: File): Promise<ProcessingResponse>

  // Procesar múltiples documentos
  processPersonDocuments(
    files: File[],
    personId: string
  ): Promise<ConsolidatedProcessingResponse>

  // Obtener resultado por ID
  getResult(id: string): Promise<HistoriaClinicaProcesada>

  // Obtener todos los resultados
  getAllResults(): Promise<HistoriaClinicaProcesada[]>
}
```

### Export Service

```typescript
// services/export.service.ts

export const exportService = {
  // Exportar a Excel
  exportToExcel(resultIds: string[]): Promise<Blob>

  // Exportar a Narah format
  exportToNarah(resultIds: string[]): Promise<Blob>
}
```

### Stats Service

```typescript
// services/stats.service.ts

export const statsService = {
  // Obtener estadísticas generales
  getStatistics(): Promise<StatisticsResponse>
}
```

---

## 🗄️ Estado Global

### ProcessingContext

```typescript
interface ProcessingContextValue {
  // State
  isProcessing: boolean;
  progress: number;
  currentFile?: string;
  error?: string;

  // Actions
  processFiles: (
    files: File[],
    personId?: string
  ) => Promise<void>;

  resetProcessing: () => void;
}
```

### ResultsContext

```typescript
interface ResultsContextValue {
  // State
  results: HistoriaClinicaProcesada[];
  currentResult?: HistoriaClinicaProcesada;
  filters: ResultsFilters;
  loading: boolean;

  // Actions
  fetchResults: () => Promise<void>;
  fetchResultById: (id: string) => Promise<void>;
  setFilters: (filters: ResultsFilters) => void;
  addResult: (result: HistoriaClinicaProcesada) => void;
}
```

---

## 🎯 Próximos Pasos de Implementación

### Fase 1: Fundamentos ✅
- [x] TypeScript types (medical.ts, components.ts)
- [x] Arquitectura documentada
- [ ] Tema Material UI actualizado
- [ ] Componentes common base

### Fase 2: Core Features
- [ ] Upload flow completo
- [ ] Results list & detail
- [ ] API services
- [ ] Contexts & hooks

### Fase 3: Polish
- [ ] Export functionality
- [ ] Stats dashboard
- [ ] Loading states
- [ ] Error handling

### Fase 4: Testing & Deployment
- [ ] Unit tests
- [ ] Integration tests
- [ ] Build optimization
- [ ] Deployment

---

**Documento creado:** 2024-11-15
**Versión:** 1.0.0
**Autor:** Claude Code Agent
