import React from 'react';
export const Separator: React.FC<{ className?: string }> = ({ className = '' }) => <hr className={`border-gray-200 ${className}`} />;
