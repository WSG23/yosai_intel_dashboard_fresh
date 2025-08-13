import React from 'react';

export interface ButtonProps {
  children: React.ReactNode;
  disabled?: boolean;
  variant?: 'default' | 'outline';
  className?: string;
  size?: 'sm' | 'default';
  onClick?: () => void;
  onPress?: () => void;
}
