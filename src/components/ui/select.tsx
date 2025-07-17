import React from 'react';
export const Select: React.FC<{ value: string; onValueChange: (value: string) => void; children: React.ReactNode }> = ({ children }) => <div className="relative">{children}</div>;
export const SelectTrigger: React.FC<{ className?: string; children: React.ReactNode }> = ({ className = '', children }) => <div className={`border rounded px-3 py-2 ${className}`}>{children}</div>;
export const SelectValue: React.FC<{ placeholder?: string }> = ({ placeholder }) => <span className="text-gray-500">{placeholder}</span>;
export const SelectContent: React.FC<{ children: React.ReactNode }> = ({ children }) => <div className="absolute z-10 bg-white border rounded shadow-lg">{children}</div>;
export const SelectItem: React.FC<{ value: string; children: React.ReactNode }> = ({ children }) => <div className="px-3 py-2 hover:bg-gray-100 cursor-pointer">{children}</div>;
