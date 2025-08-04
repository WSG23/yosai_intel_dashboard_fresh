import React, { createContext, useContext, useState, useEffect } from 'react';

interface NavbarTitleContextValue {
  title: string;
  setTitle: (title: string) => void;
}

const NavbarTitleContext = createContext<NavbarTitleContextValue | undefined>(undefined);

export const NavbarTitleProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [title, setTitle] = useState('');
  return (
    <NavbarTitleContext.Provider value={{ title, setTitle }}>
      {children}
    </NavbarTitleContext.Provider>
  );
};

export const useNavbarTitle = () => {
  const ctx = useContext(NavbarTitleContext);
  if (!ctx) {
    throw new Error('useNavbarTitle must be used within a NavbarTitleProvider');
  }
  return ctx;
};

export const NavbarTitleUpdater: React.FC<{ title: string }> = ({ title }) => {
  const { setTitle } = useNavbarTitle();
  useEffect(() => setTitle(title), [title, setTitle]);
  return null;
};
