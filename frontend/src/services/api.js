import axios from 'axios';
const API_BASE_URL = '/api/v1';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
});

export const getAvailableTests = () => apiClient.get('/tests/');
export const getQuestions = (params) => apiClient.get('/questions/', { params });