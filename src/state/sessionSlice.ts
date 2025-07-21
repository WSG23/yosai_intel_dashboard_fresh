import { StateCreator } from 'zustand';

export interface SessionSlice {
  sessionId: string | null;
  setSessionId: (id: string) => void;
}

export const createSessionSlice: StateCreator<SessionSlice, [], [], SessionSlice> = (set) => ({
  sessionId: null,
  setSessionId: (id: string) => set({ sessionId: id }),
});
