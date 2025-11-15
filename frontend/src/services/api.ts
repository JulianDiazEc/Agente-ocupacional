/**
 * Cliente API configurado con Axios
 * Configuración centralizada para llamadas al backend Flask
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Base URL desde variables de entorno
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// Timeout para procesamiento (5 minutos)
const TIMEOUT = 5 * 60 * 1000; // 300000ms

/**
 * Instancia de Axios configurada
 */
const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor
 * Añade headers adicionales si es necesario
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Aquí se puede añadir auth token si es necesario
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }

    // Log en desarrollo
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error: AxiosError) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 * Maneja errores globales
 */
api.interceptors.response.use(
  (response) => {
    // Log en desarrollo
    if (import.meta.env.DEV) {
      console.log(`[API] Response:`, response.data);
    }

    return response;
  },
  (error: AxiosError) => {
    // Manejo de errores global
    if (error.response) {
      // El servidor respondió con un código de error
      console.error('[API] Response error:', {
        status: error.response.status,
        data: error.response.data,
      });

      // Errores específicos
      switch (error.response.status) {
        case 400:
          console.error('Bad Request:', error.response.data);
          break;
        case 401:
          console.error('Unauthorized');
          // Aquí se puede redirigir al login
          break;
        case 403:
          console.error('Forbidden');
          break;
        case 404:
          console.error('Not Found');
          break;
        case 413:
          console.error('File too large');
          break;
        case 500:
          console.error('Internal Server Error');
          break;
        default:
          console.error('Error:', error.message);
      }
    } else if (error.request) {
      // La petición se hizo pero no hubo respuesta
      console.error('[API] No response received:', error.request);
    } else {
      // Error al configurar la petición
      console.error('[API] Request setup error:', error.message);
    }

    return Promise.reject(error);
  }
);

/**
 * Helper para crear FormData
 */
export const createFormData = (data: Record<string, any>): FormData => {
  const formData = new FormData();

  Object.keys(data).forEach((key) => {
    const value = data[key];

    if (value instanceof FileList) {
      // Múltiples archivos
      Array.from(value).forEach((file) => {
        formData.append(`${key}[]`, file);
      });
    } else if (value instanceof File) {
      // Archivo único
      formData.append(key, value);
    } else if (Array.isArray(value)) {
      // Array de archivos
      value.forEach((item) => {
        if (item instanceof File) {
          formData.append(`${key}[]`, item);
        }
      });
    } else if (value !== null && value !== undefined) {
      // Valores normales
      formData.append(key, value.toString());
    }
  });

  return formData;
};

/**
 * Helper para descargar archivos
 */
export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default api;
