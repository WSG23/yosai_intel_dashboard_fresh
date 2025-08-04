import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface HistoryState<T = unknown> {
  past: T[];
  present: T | null;
  future: T[];
}

const initialState: HistoryState = {
  past: [],
  present: null,
  future: [],
};

const historySlice = createSlice({
  name: 'history',
  initialState,
  reducers: {
    push(state, action: PayloadAction<unknown>) {
      if (state.present !== null) {
        state.past.push(state.present);
      }
      state.present = action.payload;
      state.future = [];
    },
    undo(state) {
      const previous = state.past.pop();
      if (previous !== undefined) {
        if (state.present !== null) {
          state.future.unshift(state.present);
        }
        state.present = previous;
      }
    },
    redo(state) {
      const next = state.future.shift();
      if (next !== undefined) {
        if (state.present !== null) {
          state.past.push(state.present);
        }
        state.present = next;
      }
    },
  },
});

export const { push, undo, redo } = historySlice.actions;
export default historySlice.reducer;
