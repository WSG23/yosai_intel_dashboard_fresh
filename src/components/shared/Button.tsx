import React from 'react';

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  icon?: React.ReactNode;
}

export const Button: React.FC<Props> = ({ variant = 'primary', icon, children, className = '', ...rest }) => {
  const base = 'px-4 py-2 rounded-md text-sm font-medium focus:outline-none';
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
  };
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...rest}>
      {icon && <span className="mr-2 inline-flex">{icon}</span>}
      {children}
    </button>
  );
};
