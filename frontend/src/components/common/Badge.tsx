import React from 'react';
import { BadgeProps } from '@/types';

/**
 * Badge component para estados y etiquetas
 * Variantes: success (green), warning (yellow), error (red), info (blue), default (gray)
 */
export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  icon,
  children,
  className = '',
  dot = false,
}) => {
  // Base classes
  const baseClasses = 'inline-flex items-center font-medium rounded-full transition-colors';

  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-3 py-1 text-xs gap-1.5',
    lg: 'px-4 py-1.5 text-sm gap-2',
  };

  // Variant classes
  const variantClasses = {
    success: 'bg-green-100 text-green-800 border border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    error: 'bg-red-100 text-red-800 border border-red-200',
    info: 'bg-blue-100 text-blue-800 border border-blue-200',
    default: 'bg-gray-100 text-gray-800 border border-gray-200',
  };

  // Dot color classes
  const dotColorClasses = {
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    default: 'bg-gray-500',
  };

  // Combine classes
  const badgeClasses = `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`;

  return (
    <span className={badgeClasses}>
      {dot && (
        <span className={`w-2 h-2 rounded-full ${dotColorClasses[variant]}`} />
      )}
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

export default Badge;
