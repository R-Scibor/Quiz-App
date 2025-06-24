import axios from 'axios';

// Konfiguracja instancji axios do komunikacji z API backendu.
const apiClient = axios.create({
    baseURL: '/api/v1', // Używamy relatywnej ścieżki, aby Vite proxy mogło działać
    headers: {
        'Content-Type': 'application/json',
    }
});

// Interceptor pozwala na globalne przechwytywanie i obsługę odpowiedzi
// zanim zostaną one przekazane do bloku .then() lub .catch() w miejscu wywołania.

apiClient.interceptors.response.use(
    // Funkcja dla pomyślnych odpowiedzi (status 2xx) - po prostu je zwracamy.
    (response) => response,

    // Funkcja dla odpowiedzi z błędem (status inny niż 2xx).
    (error) => {
        let structuredError = {
            message: 'Wystąpił nieoczekiwany błąd. Proszę spróbować ponownie.',
            details: null,
            code: 'UNKNOWN_ERROR'
        };

        // Sprawdzamy, czy błąd pochodzi z odpowiedzi serwera (ma status code)
        if (error.response) {
            const backendError = error.response.data;
            // Sprawdzamy, czy odpowiedź serwera ma oczekiwany format { error, message }
            if (backendError && backendError.message) {
                structuredError.message = backendError.message;
                structuredError.code = backendError.error || `HTTP_${error.response.status}`;
            } else {
                // Jeśli format jest inny, używamy generycznej wiadomości dla danego kodu HTTP
                structuredError.message = `Błąd serwera: Otrzymano status ${error.response.status}.`;
                structuredError.code = `HTTP_${error.response.status}`;
            }
            structuredError.details = backendError;
        } else if (error.request) {
            // Błąd sieciowy - zapytanie zostało wysłane, ale nie otrzymano odpowiedzi
            structuredError.message = 'Błąd połączenia z serwerem. Sprawdź swoje połączenie internetowe.';
            structuredError.code = 'NETWORK_ERROR';
        } else {
            // Inny, nieprzewidziany błąd (np. błąd w konfiguracji zapytania)
            structuredError.message = error.message;
        }

        // Zwracamy Promise.reject z naszym nowym, ustrukturyzowanym obiektem błędu.
        // Dzięki temu w bloku .catch() w store otrzymamy ten właśnie obiekt.
        return Promise.reject(structuredError);
    }
);

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
