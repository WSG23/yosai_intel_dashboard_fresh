import axios from 'axios';

// Configure axios defaults
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token if available
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const uploadAPI = {
    processFile: (formData: FormData) =>
        api.post('/upload/process', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        }),

    saveMappings: (data: any) =>
        api.post('/mappings/save', data),

    loadMappings: (fingerprint: string) =>
        api.get(`/mappings/load/${fingerprint}`),

    getProgress: (taskId: string) =>
        api.get(`/upload/progress/${taskId}`),
};

export default api;