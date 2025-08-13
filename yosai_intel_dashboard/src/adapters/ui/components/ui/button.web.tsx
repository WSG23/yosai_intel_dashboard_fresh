import React from 'react';
import type { ButtonProps } from './button.types';

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  disabled = false,
  variant = 'default',
  className = '',
  size = 'default',
}) => {
  const baseClass =
    size === 'sm'
      ? 'px-3 py-1 text-sm rounded font-medium'
      : 'px-4 py-2 rounded-lg font-medium';
  const variantClass =
    variant === 'outline'
      ? 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
      : 'bg-blue-600 text-white hover:bg-blue-700';
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClass} ${variantClass} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children}
    </button>
  );
};
