import React from 'react';
import type { ButtonProps } from './button.types';
import { Button as WebButton } from './button.web';
import { Button as NativeButton } from './button.native';

export { type ButtonProps };

export const Button: React.FC<ButtonProps> = (props) => {
  const isWeb = typeof document !== 'undefined';
  if (isWeb) {
    return <WebButton {...props} />;
  }
  return <NativeButton {...props} />;
};
