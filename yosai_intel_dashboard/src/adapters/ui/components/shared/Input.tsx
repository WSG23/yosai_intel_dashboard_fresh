import React from 'react';

interface Props extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

export const Input: React.FC<Props> = ({ className = '', ...rest }) => {
  return (
    <input
      className={`border rounded-md px-2 py-1 ${className}`}
      {...rest}
    />
  );
};
