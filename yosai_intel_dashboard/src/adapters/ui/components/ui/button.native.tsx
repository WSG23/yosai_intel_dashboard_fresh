import React from 'react';
import { Pressable, Text } from 'react-native';
import type { ButtonProps } from './button.types';

export const Button: React.FC<ButtonProps> = ({
  children,
  onPress,
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
    <Pressable
      onPress={onPress}
      disabled={disabled}
      className={`${baseClass} ${variantClass} ${disabled ? 'opacity-50' : ''} ${className}`}
    >
      {typeof children === 'string' ? <Text>{children}</Text> : children}
    </Pressable>
  );
};
