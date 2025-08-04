import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SelectionState {
  selectedThreats: string[];
  selectedRange: [number, number] | null;
}

const initialState: SelectionState = {
  selectedThreats: [],
  selectedRange: null,
};

const selectionSlice = createSlice({
  name: 'selection',
  initialState,
  reducers: {
    setSelectedThreats(state, action: PayloadAction<string[]>) {
      state.selectedThreats = action.payload;
    },
    setSelectedRange(state, action: PayloadAction<[number, number] | null>) {
      state.selectedRange = action.payload;
    },
  },
});

export const { setSelectedThreats, setSelectedRange } = selectionSlice.actions;
export default selectionSlice.reducer;
