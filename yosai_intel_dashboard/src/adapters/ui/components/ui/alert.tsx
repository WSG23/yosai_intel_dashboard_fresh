import React from 'react';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({ children, className = '', ...props }) => (
  <div
    role="alert"
    aria-live="assertive"
    className={`border rounded-lg p-4 ${className}`}
    {...props}
  >
    {children}
  </div>
);

interface AlertDescriptionProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ children, className = '', ...props }) => (
  <div className={className} {...props}>
    {children}
  </div>
);
