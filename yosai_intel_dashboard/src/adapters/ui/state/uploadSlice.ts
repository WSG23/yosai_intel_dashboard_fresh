import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UploadedFile } from '../components/upload/types';

export interface UploadState {
  uploadedFiles: UploadedFile[];
}

const initialState: UploadState = {
  uploadedFiles: [],
};

const uploadSlice = createSlice({
  name: 'upload',
  initialState,
  reducers: {
    setUploadedFiles(state, action: PayloadAction<UploadedFile[]>) {
      state.uploadedFiles = action.payload;
    },
  },
});

export const { setUploadedFiles } = uploadSlice.actions;
export default uploadSlice.reducer;
