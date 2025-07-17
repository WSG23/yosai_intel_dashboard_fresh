import React from 'react';
export const Badge: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => <span className={`px-2 py-1 text-xs rounded-full ${className}`}>{children}</span>;
