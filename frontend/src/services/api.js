import axios from 'axios';

// Konfiguracja instancji axios do komunikacji z API backendu.
const apiClient = axios.create({
    baseURL: '/api/v1', // Używamy relatywnej ścieżki, aby Vite proxy mogło działać
    headers: {
        'Content-Type': 'application/json',
    }
});

/**
 * Pobiera listę wszystkich dostępnych testów i ich metadanych.
 * @returns {Promise} Obietnica z odpowiedzią API.
 */
export const getAvailableTests = () => {
    return apiClient.get('/tests/');
};

/**
 * Pobiera określoną liczbę pytań z wybranych kategorii.
 * @param {object} params - Parametry zapytania.
 * @param {string} params.categories - ID kategorii oddzielone przecinkami.
 * @param {number} params.num_questions - Żądana liczba pytań.
 * @param {string} params.mode - Tryb pytań ('closed', 'open', 'mixed').
 * @returns {Promise} Obietnica z odpowiedzią API zawierającą pytania.
 */
export const getQuestions = (params) => {
    return apiClient.get('/questions/', { params });
};


/**
 * Wysyła odpowiedź na pytanie otwarte do oceny przez AI.
 * @param {object} payload - Dane do wysłania.
 * @param {string} payload.questionText - Treść pytania.
 * @param {string} payload.userAnswer - Odpowiedź udzielona przez użytkownika.
 * @param {string} payload.gradingCriteria - Kryteria oceny zdefiniowane dla pytania.
 * @param {number} payload.maxPoints - Maksymalna liczba punktów za pytanie.
 * @returns {Promise} Obietnica z odpowiedzią API zawierającą ocenę.
 */
export const checkOpenAnswer = (payload) => {
    return apiClient.post('/check_answer/', payload);
};
