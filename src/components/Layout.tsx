import React from 'react';
import { Header } from './Navigation';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto p-4">{children}</main>
    </div>
  );
};

export default Layout;
