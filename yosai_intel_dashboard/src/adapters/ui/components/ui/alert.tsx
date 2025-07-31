import React from 'react';
export const Alert: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => <div className={`border rounded-lg p-4 ${className}`}>{children}</div>;
export const AlertDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => <div className={className}>{children}</div>;
