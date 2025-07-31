import React, { createContext, useContext } from 'react';
import { boundStore, BoundState } from './store';
import { useStore } from 'zustand';

const ZustandContext = createContext(boundStore);

export const ZustandProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ZustandContext.Provider value={boundStore}>{children}</ZustandContext.Provider>
);

export const useZustandStore = <T,>(selector: (state: BoundState) => T) =>
  useStore(useContext(ZustandContext), selector);
