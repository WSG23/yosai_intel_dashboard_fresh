import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SessionState {
  sessionId: string | null;
}

const initialState: SessionState = {
  sessionId: null,
};

const sessionSlice = createSlice({
  name: 'session',
  initialState,
  reducers: {
    setSessionId(state, action: PayloadAction<string>) {
      state.sessionId = action.payload;
    },
  },
});

export const { setSessionId } = sessionSlice.actions;
export default sessionSlice.reducer;
