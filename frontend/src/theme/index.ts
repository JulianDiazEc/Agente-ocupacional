import { createTheme } from '@mui/material/styles'

/**
 * Tema personalizado de Narah Metrics
 * Paleta principal: Pink (#EC4899)
 * Basado en diseños existentes (ResultadosDemo.jsx y VisorDocumentosMedicos.tsx)
 */

export const theme = createTheme({
  palette: {
    // Brand color: Pink (Narah Metrics)
    primary: {
      main: '#EC4899',      // pink-500
      light: '#F9A8D4',     // pink-300
      dark: '#BE185D',      // pink-700
      contrastText: '#FFFFFF',
    },

    // Secondary: Neutral gray
    secondary: {
      main: '#6B7280',      // gray-500
      light: '#9CA3AF',     // gray-400
      dark: '#374151',      // gray-700
      contrastText: '#FFFFFF',
    },

    // Success: Green
    success: {
      main: '#22C55E',      // green-500
      light: '#86EFAC',     // green-300
      dark: '#15803D',      // green-700
      contrastText: '#FFFFFF',
    },

    // Warning: Yellow
    warning: {
      main: '#EAB308',      // yellow-500
      light: '#FDE047',     // yellow-300
      dark: '#A16207',      // yellow-700
      contrastText: '#111827',
    },

    // Error: Red
    error: {
      main: '#EF4444',      // red-500
      light: '#FCA5A5',     // red-300
      dark: '#B91C1C',      // red-700
      contrastText: '#FFFFFF',
    },

    // Info: Blue
    info: {
      main: '#3B82F6',      // blue-500
      light: '#93C5FD',     // blue-300
      dark: '#1E40AF',      // blue-700
      contrastText: '#FFFFFF',
    },

    // Backgrounds
    background: {
      default: '#F9FAFB',   // gray-50
      paper: '#FFFFFF',
    },

    // Text
    text: {
      primary: '#111827',   // gray-900
      secondary: '#6B7280', // gray-500
      disabled: '#D1D5DB',  // gray-300
    },

    // Divider
    divider: '#E5E7EB',     // gray-200
  },

  // Typography
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),

    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      color: '#111827',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
      color: '#111827',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.3,
      color: '#111827',
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: '#111827',
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: '#111827',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
      color: '#111827',
    },

    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      color: '#111827',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      color: '#6B7280',
    },

    button: {
      textTransform: 'none',
      fontWeight: 500,
    },

    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.5,
      color: '#6B7280',
    },
  },

  // Shape
  shape: {
    borderRadius: 8,
  },

  // Shadows (más sutiles)
  shadows: [
    'none',
    '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  ],

  // Component overrides
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 500,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
          },
        },
        outlined: {
          borderWidth: 1,
        },
      },
      defaultProps: {
        disableElevation: true,
      },
    },

    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
          border: '1px solid #E5E7EB',
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
        elevation1: {
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        },
      },
    },

    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          fontWeight: 500,
        },
      },
    },

    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },

    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },

    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
        },
      },
    },

    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },

    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #E5E7EB',
        },
        head: {
          fontWeight: 600,
          color: '#6B7280',
          backgroundColor: '#F9FAFB',
        },
      },
    },
  },
})
