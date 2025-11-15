import React from 'react';
import { CardProps } from '@/types';

/**
 * Card component reutilizable
 * Variantes: default, elevated, outlined, filled
 */
export const Card: React.FC<CardProps> = ({
  variant = 'default',
  title,
  subtitle,
  icon,
  headerAction,
  action,
  children,
  className = '',
  hoverable = false,
  onClick,
}) => {
  // Base classes
  const baseClasses = 'rounded-xl overflow-hidden transition-all duration-200';

  // Variant classes
  const variantClasses = {
    default: 'bg-white border border-gray-200 shadow-sm',
    elevated: 'bg-white shadow-md',
    outlined: 'bg-white border-2 border-gray-300',
    filled: 'bg-gray-50 border border-gray-200',
  };

  // Hoverable effect
  const hoverClasses = hoverable ? 'hover:shadow-lg hover:border-pink-200 cursor-pointer' : '';

  // Combine classes
  const cardClasses = `${baseClasses} ${variantClasses[variant]} ${hoverClasses} ${className}`;
  const headerSlot = headerAction ?? action;

  return (
    <div
      className={cardClasses}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {/* Header */}
      {(title || subtitle || icon || headerSlot) && (
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-pink-50/30 to-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1">
              {/* Icon */}
              {icon && (
                <div className="w-8 h-8 bg-pink-100 rounded-lg flex items-center justify-center flex-shrink-0 text-pink-600">
                  {icon}
                </div>
              )}

              {/* Title & Subtitle */}
              <div className="flex-1 min-w-0">
                {title && (
                  <h2 className="text-xl font-bold text-gray-900 truncate">
                    {title}
                  </h2>
                )}
                {subtitle && (
                  <p className="text-sm text-gray-500 mt-0.5 truncate">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>

            {/* Header Action */}
            {headerSlot && (
              <div className="ml-4 flex-shrink-0">
                {headerSlot}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};

export default Card;
