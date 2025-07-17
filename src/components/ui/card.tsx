import React from 'react';
export const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => <div className={`bg-white rounded-lg shadow ${className}`}>{children}</div>;
export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => <div className={`px-6 py-4 border-b ${className}`}>{children}</div>;
export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => <h3 className={`text-lg font-semibold ${className}`}>{children}</h3>;
export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => <div className={`px-6 py-4 ${className}`}>{children}</div>;
