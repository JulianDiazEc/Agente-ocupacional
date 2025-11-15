/**
 * Tipos para componentes reutilizables de la UI
 */

import { ReactNode } from 'react';
import { SeveridadAlerta } from './medical';

// ============================================================================
// TIPOS DE BOTONES
// ============================================================================

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

// ============================================================================
// TIPOS DE CARDS
// ============================================================================

export type CardVariant = 'default' | 'elevated' | 'outlined' | 'filled';

export interface CardProps {
  variant?: CardVariant;
  title?: string;
  subtitle?: string;
  icon?: ReactNode;
  headerAction?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  onClick?: () => void;
}

// ============================================================================
// TIPOS DE BADGES
// ============================================================================

export type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'default';
export type BadgeSize = 'sm' | 'md' | 'lg';

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  dot?: boolean;
}

// ============================================================================
// TIPOS DE ALERTAS
// ============================================================================

export interface AlertProps {
  severity: SeveridadAlerta;
  title?: string;
  message?: string;
  onClose?: () => void;
  closeable?: boolean;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
  children?: ReactNode;
}

// ============================================================================
// TIPOS DE BANNERS
// ============================================================================

export type BannerType = 'success' | 'error' | 'warning' | 'info';

export interface BannerProps {
  type: BannerType;
  title: string;
  message?: string;
  onClose?: () => void;
  children?: ReactNode;
  className?: string;
}

// ============================================================================
// TIPOS DE TABLAS
// ============================================================================

export interface Column<T> {
  key: keyof T | string;
  label: string;
  width?: string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  render?: (value: any, row: T) => ReactNode;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  onRowClick?: (row: T) => void;
  selectedRows?: T[];
  onSelectionChange?: (rows: T[]) => void;
  emptyMessage?: string;
  className?: string;
}

// ============================================================================
// TIPOS DE MODAL
// ============================================================================

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  size?: ModalSize;
  children: ReactNode;
  footer?: ReactNode;
  closeOnBackdrop?: boolean;
  className?: string;
}

// ============================================================================
// TIPOS DE TABS
// ============================================================================

export interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  badge?: number;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'default' | 'pills' | 'underline';
  className?: string;
}

// ============================================================================
// TIPOS DE INPUTS
// ============================================================================

export type InputType = 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';

export interface InputProps {
  type?: InputType;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  icon?: ReactNode;
  className?: string;
}

// ============================================================================
// TIPOS DE FILE UPLOAD
// ============================================================================

export interface FileUploadProps {
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // en MB
  maxFiles?: number;
  onFilesChange: (files: File[]) => void;
  files?: File[];
  error?: string;
  disabled?: boolean;
  className?: string;
}

export interface UploadedFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

// ============================================================================
// TIPOS DE DROPDOWN/SELECT
// ============================================================================

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  icon?: ReactNode;
}

export interface SelectProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  searchable?: boolean;
  className?: string;
}

// ============================================================================
// TIPOS DE PROGRESS BAR
// ============================================================================

export type ProgressVariant = 'default' | 'success' | 'warning' | 'error';

export interface ProgressProps {
  value: number; // 0-100
  variant?: ProgressVariant;
  showLabel?: boolean;
  label?: string;
  indeterminate?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// ============================================================================
// TIPOS DE TOOLTIP
// ============================================================================

export type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right';

export interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  placement?: TooltipPlacement;
  className?: string;
}

// ============================================================================
// TIPOS DE SKELETON LOADER
// ============================================================================

export type SkeletonVariant = 'text' | 'rectangular' | 'circular';

export interface SkeletonProps {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  className?: string;
}

// ============================================================================
// TIPOS DE PAGINATION
// ============================================================================

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
  onPageSizeChange?: (size: number) => void;
  totalItems?: number;
  className?: string;
}

// ============================================================================
// TIPOS DE STATS CARD
// ============================================================================

export interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

// ============================================================================
// TIPOS DE EMPTY STATE
// ============================================================================

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  message?: string;
  action?: ReactNode;
  className?: string;
}

// ============================================================================
// TIPOS DE BREADCRUMBS
// ============================================================================

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: ReactNode;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}
