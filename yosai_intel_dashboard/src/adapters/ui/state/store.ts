import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import sessionReducer from './sessionSlice';
import analyticsReducer from './analyticsSlice';
import uploadReducer from './uploadSlice';
import selectionReducer from './selectionSlice';
import historyReducer from './historySlice';

export const store = configureStore({
  reducer: {
    session: sessionReducer,
    analytics: analyticsReducer,
    upload: uploadReducer,
    selection: selectionReducer,
    history: historyReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
