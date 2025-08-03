import React, { createContext, useContext, useState, ReactNode } from 'react';

export type SelectionState = Record<string, unknown>;

export interface SelectionContextValue {
  selections: SelectionState;
  select: (key: string, value: unknown) => void;
  clear: (key?: string) => void;
}

const SelectionContext = createContext<SelectionContextValue | undefined>(undefined);

export const SelectionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [selections, setSelections] = useState<SelectionState>({});

  const select = (key: string, value: unknown) => {
    setSelections((prev) => ({ ...prev, [key]: value }));
  };

  const clear = (key?: string) => {
    if (key) {
      setSelections((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    } else {
      setSelections({});
    }
  };

  return (
    <SelectionContext.Provider value={{ selections, select, clear }}>
      {children}
    </SelectionContext.Provider>
  );
};

export const useSelection = (): SelectionContextValue => {
  const context = useContext(SelectionContext);
  if (!context) {
    throw new Error('useSelection must be used within a SelectionProvider');
  }
  return context;
};

