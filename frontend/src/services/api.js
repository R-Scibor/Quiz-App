import axios from 'axios';

// Axios instance for all backend API calls.
const apiClient = axios.create({
    baseURL: '/api/v1', // Relative base URL so the Vite proxy works in development.
    headers: {
        'Content-Type': 'application/json',
    }
});

let unauthorizedHandler = null;

export const setUnauthorizedHandler = (fn) => {
    unauthorizedHandler = fn;
};

/**
 * True when a 401 means the stored token is no longer valid.
 * Login/register 401s are bad credentials. Logout 401s must not re-enter the handler.
 */
export const shouldTreatAsExpiredSession = ({ status, url = '', hasToken }) => {
    if (status !== 401 || !hasToken) return false;
    if (
        url.includes('/auth/login') ||
        url.includes('/auth/register') ||
        url.includes('/auth/logout')
    ) {
        return false;
    }
    return true;
};

// Inject auth token from localStorage into every request.
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    return config;
});

// Normalise all error responses into a consistent shape before
// they reach the calling .catch() blocks.

apiClient.interceptors.response.use(
    // Pass successful responses through unchanged.
    (response) => response,

    // Normalise error responses.
    (error) => {
        let structuredError = {
            message: 'An unexpected error occurred. Please try again.',
            details: null,
            code: 'UNKNOWN_ERROR'
        };

        // Server responded with a non-2xx status code.
        if (error.response) {
            const backendError = error.response.data;
            // Backend returned the expected { error, message } shape.
            if (backendError && backendError.message) {
                structuredError.message = backendError.message;
                structuredError.code = backendError.error || `HTTP_${error.response.status}`;
            } else {
                // Fallback for responses that don't match the expected shape.
                structuredError.message = `Server error: received status ${error.response.status}.`;
                structuredError.code = `HTTP_${error.response.status}`;
            }
            structuredError.details = backendError;

            if (shouldTreatAsExpiredSession({
                status: error.response.status,
                url: error.config?.url || '',
                hasToken: Boolean(localStorage.getItem('auth_token')),
            })) {
                unauthorizedHandler?.();
            }
        } else if (error.request) {
            // Request was sent but no response was received (network error).
            structuredError.message = 'Could not connect to the server. Check your internet connection.';
            structuredError.code = 'NETWORK_ERROR';
        } else {
            // Unexpected error (e.g. misconfigured request).
            structuredError.message = error.message;
        }

        // Reject with the structured error so store .catch() blocks receive a consistent shape.
        return Promise.reject(structuredError);
    }
);

/**
 * Fetches all available tests and their metadata.
 * @returns {Promise} API response.
 */
export const getAvailableTests = () => {
    return apiClient.get('/tests/');
};

/**
 * Fetches a randomised set of questions from the selected categories.
 * @param {object} params - Query parameters.
 * @param {string} params.categories - Comma-separated test IDs.
 * @param {number} params.num_questions - Number of questions to return.
 * @param {string} params.mode - Question type filter ('closed', 'open', 'mixed').
 * @returns {Promise} API response containing the question list.
 */
export const getQuestions = (params) => {
    return apiClient.get('/questions/', { params });
};


/**
 * Submits an open-ended answer for AI grading.
 * @param {object} payload - Request payload.
 * @param {string} payload.questionText - The question text.
 * @param {string} payload.userAnswer - The user's answer.
 * @param {string} payload.gradingCriteria - Grading criteria for the question.
 * @param {number} payload.maxPoints - Maximum points for the question.
 * @returns {Promise} API response containing the grading result.
 */
export const checkOpenAnswer = (payload) => {
    return apiClient.post('/check_answer/', payload);
};

/**
 * Polls the status of an async grading task.
 * @param {string} taskId - Task ID returned by checkOpenAnswer.
 * @returns {Promise} API response containing the task status and result.
 */
export const getTaskResult = (taskId) => {
    return apiClient.get(`/task_result/${taskId}/`);
};


/**
 * Submits a reported issue for a question or AI grading result.
 * @param {object} payload - Issue payload.
 * @param {string} payload.question - Question ID.
 * @param {string} payload.test - Test ID.
 * @param {string} payload.issue_type - Issue type ('QUESTION_ERROR' or 'AI_GRADING_ERROR').
 * @param {string} [payload.description] - Optional user description.
 * @param {string} [payload.ai_feedback_snapshot] - Saved AI response (required for AI_GRADING_ERROR).
 * @returns {Promise} API response.
 */
export const reportIssue = (payload) => {
    return apiClient.post('/report_issue/', payload);
};

export const startSession = (payload = {}) => {
    return apiClient.post('/sessions/start/', payload);
};

export const completeSession = (sessionId, payload) => {
    return apiClient.post(`/sessions/${sessionId}/complete/`, payload);
};

export const submitAttempts = (attempts) => {
    return apiClient.post('/attempts/', attempts);
};

export const getUserStats = () => {
    return apiClient.get('/stats/');
};

export const getStudyQueue = (limit = 20, testIds = null) => {
    const params = { limit };
    if (testIds && testIds.length > 0) params.test_ids = testIds.join(',');
    return apiClient.get('/study/queue/', { params });
};

export const getStudyStats = () => {
    return apiClient.get('/study/stats/');
};

export const getTestStats = () => {
    return apiClient.get('/stats/tests/');
};

export const registerUser = (payload) => {
    return apiClient.post('/auth/register/', payload);
};

export const loginUser = (payload) => {
    return apiClient.post('/auth/login/', payload);
};

export const logoutUser = () => {
    return apiClient.post('/auth/logout/');
};
