import React from 'react';
export const Tabs: React.FC<{ value: string; onValueChange: (value: string) => void; className?: string; children: React.ReactNode }> = ({ children, className = '' }) => <div className={className}>{children}</div>;
export const TabsList: React.FC<{ className?: string; children: React.ReactNode }> = ({ children, className = '' }) => <div className={`flex ${className}`}>{children}</div>;
export const TabsTrigger: React.FC<{ value: string; className?: string; children: React.ReactNode }> = ({ children, className = '' }) => <button className={`px-4 py-2 ${className}`}>{children}</button>;
export const TabsContent: React.FC<{ value: string; className?: string; children: React.ReactNode }> = ({ children, className = '' }) => <div className={className}>{children}</div>;
