import React from 'react';
import { AlertCircle, CheckCircle, AlertTriangle, Info, X } from 'lucide-react';
import { AlertProps } from '@/types';

/**
 * Alert component para notificaciones y mensajes
 * Severidades: alta (red), media (yellow), baja (blue)
 */
export const Alert: React.FC<AlertProps> = ({
  severity,
  title,
  message,
  onClose,
  closeable = true,
  icon,
  action,
  className = '',
}) => {
  // Severity to variant mapping
  const severityConfig = {
    alta: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      iconColor: 'text-red-500',
      titleColor: 'text-red-800',
      messageColor: 'text-red-700',
      icon: <AlertCircle size={20} />,
    },
    media: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      iconColor: 'text-yellow-500',
      titleColor: 'text-yellow-800',
      messageColor: 'text-yellow-700',
      icon: <AlertTriangle size={20} />,
    },
    baja: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      iconColor: 'text-blue-500',
      titleColor: 'text-blue-800',
      messageColor: 'text-blue-700',
      icon: <Info size={20} />,
    },
  };

  const config = severityConfig[severity];

  return (
    <div className={`rounded-lg border p-4 ${config.bg} ${config.border} ${className}`}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={`flex-shrink-0 mt-0.5 ${config.iconColor}`}>
          {icon || config.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {title && (
            <h4 className={`font-semibold mb-1 ${config.titleColor}`}>
              {title}
            </h4>
          )}
          {message && (
            <p className={`text-sm ${config.messageColor}`}>
              {message}
            </p>
          )}
          {action && (
            <div className="mt-3">
              {action}
            </div>
          )}
        </div>

        {/* Close button */}
        {closeable && onClose && (
          <button
            onClick={onClose}
            className={`flex-shrink-0 ${config.iconColor} hover:opacity-70 transition-opacity`}
          >
            <X size={18} />
          </button>
        )}
      </div>
    </div>
  );
};

export default Alert;
