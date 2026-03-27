import { create } from 'zustand';
import { getAvailableTests, getQuestions, checkOpenAnswer as checkOpenAnswerApi, getTaskResult as getTaskResultApi, registerUser, loginUser, logoutUser, startSession, completeSession, submitAttempts, getUserStats, getStudyQueue } from '../services/api';

const initialTheme = localStorage.getItem('theme') || 'dark';

const useTestStore = create((set, get) => ({
    // State properties
    view: 'home',
    availableTests: [],
    selectedCategories: [],
    numQuestionsConfig: 10,
    timerEnabled: false,
    questionMode: 'closed',

    currentQuestions: [],
    currentQuestionIndex: 0,
    userAnswers: {},
    score: 0,
    testStartTime: null,
    testEndTime: null,
    isLoading: false,
    error: null,
    theme: initialTheme,
    isTimerRunning: false, // New state to control timer
    questionStartTime: null, // New state to mark when current question started
    totalTimeSpent: 0, // New state to accumulate time spent on questions

    checkingQuestionId: null, // Will hold the ID of the question being graded
    openQuestionResults: {}, // Will store all feedback permanently
    questionTimes: {}, // Per-question time tracking { questionId: seconds }

    // Auth state
    user: null,
    authToken: null,
    isAuthLoading: false,
    authError: null,

    // Session / stats state
    currentSessionId: null,
    userStats: null,
    statsLoading: false,

    // Spaced repetition state
    difficultyRatings: {},   // { questionId: 'easy' | 'normal' | 'hard' }
    studyQueueCount: null,   // number of due questions for home page badge

    // Actions
    goToSetup: () => set({ view: 'setup' }),

    fetchAvailableTests: async () => {
        set({ isLoading: true, error: null });
        try {
            const response = await getAvailableTests();
            const tests = response.data.map(test => ({ ...test, question_counts: test.question_counts || { closed: 0, open: 0, total: 0 } }));
            set({ availableTests: tests, isLoading: false });
        } catch (error) {
            console.error("Błąd podczas pobierania testów:", error);
            set({ error: error, isLoading: false });
        }
    },

    toggleCategory: (categoryId) => set((state) => {
        const selected = new Set(state.selectedCategories);
        if (selected.has(categoryId)) selected.delete(categoryId);
        else selected.add(categoryId);
        return { selectedCategories: Array.from(selected) };
    }),

    setQuestionMode: (mode) => set({ questionMode: mode }),

    setConfig: (num, timer) => set({ numQuestionsConfig: num, timerEnabled: timer }),
    
    startTest: async () => {
        const { numQuestionsConfig, selectedCategories, questionMode } = get();
        if (selectedCategories.length === 0) {
            set({ error: { message: 'Wybierz przynajmniej jedną kategorię.', code: 'VALIDATION_ERROR' } });
            return;
        }
        set({ isLoading: true, error: null, view: 'test', score: 0, currentQuestionIndex: 0, userAnswers: {}, questionTimes: {}, currentSessionId: null });
        try {
            const response = await getQuestions({
                categories: selectedCategories.join(','),
                num_questions: numQuestionsConfig,
                mode: questionMode
            });
            set({
                currentQuestions: response.data,
                isLoading: false,
                testStartTime: new Date(),
                isTimerRunning: true,
                questionStartTime: new Date(),
            });
            if (get().user) {
                try {
                    const sessionRes = await startSession();
                    set({ currentSessionId: sessionRes.data.session_id });
                } catch (e) {
                    console.error('Failed to start session:', e);
                }
            }
        } catch (error) {
            console.error("Błąd podczas pobierania pytań:", error);
            set({ error: error, isLoading: false, view: 'setup' });
        }
    },
    
    submitAnswer: (questionId, answer) => set((state) => ({
        userAnswers: { ...state.userAnswers, [questionId]: answer },
    })),

    // Pause timer when answer is confirmed for closed questions
    confirmAnswer: () => {
        const { currentQuestionIndex, currentQuestions, userAnswers, questionStartTime } = get();
        const question = currentQuestions[currentQuestionIndex];
        const userSelection = userAnswers[question.id] || [];
        const isCorrect = JSON.stringify(userSelection.sort()) === JSON.stringify(question.correctAnswers.sort());
        if (isCorrect) set(state => ({ score: state.score + 1 }));

        if (questionStartTime) {
            const timeElapsed = Math.floor((new Date() - new Date(questionStartTime)) / 1000);
            set(state => ({
                totalTimeSpent: state.totalTimeSpent + timeElapsed,
                isTimerRunning: false,
                questionTimes: { ...state.questionTimes, [question.id]: timeElapsed },
            }));
        }
    },
    
    checkOpenAnswer: async (userAnswer) => {
        const { currentQuestionIndex, currentQuestions, questionStartTime } = get();
        const question = currentQuestions[currentQuestionIndex];

        if (questionStartTime) {
            const timeElapsed = Math.floor((new Date() - new Date(questionStartTime)) / 1000);
            set(state => ({
                totalTimeSpent: state.totalTimeSpent + timeElapsed,
                isTimerRunning: false,
                questionTimes: { ...state.questionTimes, [question.id]: timeElapsed },
            }));
        }

        // Set the specific question ID that is being checked
        set(state => ({
            checkingQuestionId: question.id,
            error: null,
            // Pre-emptively store the user's answer
            openQuestionResults: {
                ...state.openQuestionResults,
                [question.id]: {
                    ...(state.openQuestionResults[question.id] || {}),
                    userAnswer: userAnswer,
                }
            }
        }));

        const payload = {
            questionText: question.questionText,
            userAnswer: userAnswer,
            gradingCriteria: question.gradingCriteria,
            maxPoints: question.maxPoints
        };
        
        const response = await checkOpenAnswerApi(payload);
        return response.data;
    },

    getTaskResult: async (taskId) => {
        const response = await getTaskResultApi(taskId);
        return response.data; // Zwracamy { status: '...', data: '...' }
    },

    setLastAnswerFeedback: (feedbackData, questionId) => {
        const { score, feedback } = feedbackData;
        const { currentQuestions } = get();
        const question = currentQuestions.find(q => q.id === questionId);

        if (!question) return;

        set(state => ({
            score: state.score + score,
            openQuestionResults: {
                ...state.openQuestionResults,
                [questionId]: {
                    ...state.openQuestionResults[questionId],
                    points_awarded: score,
                    feedback: feedback,
                    maxPoints: question.maxPoints
                }
            },
            // Clear the checking state only if it matches the question that just finished
            checkingQuestionId: state.checkingQuestionId === questionId
                ? null
                : state.checkingQuestionId,
        }));
    },

    // Nowa akcja do obsługi błędów
    setError: (error) => {
        set({ error: error, checkingQuestionId: null });
    },

    nextQuestion: () => {
        const state = get();
        let extraTime = 0;
        if (state.questionStartTime && state.isTimerRunning) {
            extraTime = Math.floor((new Date() - new Date(state.questionStartTime)) / 1000);
        }
        set({ error: null, totalTimeSpent: state.totalTimeSpent + extraTime });

        if (state.currentQuestionIndex + 1 < state.currentQuestions.length) {
            set({
                currentQuestionIndex: state.currentQuestionIndex + 1,
                questionStartTime: new Date(),
                isTimerRunning: true,
            });
        } else {
            set({ view: 'results', testEndTime: new Date() });
            get()._finalizeSession();
        }
    },

    resetTest: () => set({
        questionMode: 'closed',
        view: 'home',
        selectedCategories: [],
        currentQuestions: [],
        currentQuestionIndex: 0,
        userAnswers: {},
        score: 0,
        testStartTime: null,
        testEndTime: null,
        error: null,
        openQuestionResults: {},
        checkingQuestionId: null,
        isTimerRunning: false,
        questionStartTime: null,
        totalTimeSpent: 0,
        questionTimes: {},
        currentSessionId: null,
        difficultyRatings: {},
    }),

    _finalizeSession: async () => {
        const { currentSessionId, user, currentQuestions, userAnswers, openQuestionResults, score, questionTimes, difficultyRatings } = get();
        if (!currentSessionId || !user) return;

        const attempts = currentQuestions.map(q => {
            let is_correct, points_awarded;
            if (q.type === 'open-ended') {
                const result = openQuestionResults[q.id];
                points_awarded = result?.points_awarded ?? 0;
                is_correct = points_awarded > 0;
            } else {
                const userSel = userAnswers[q.id] || [];
                is_correct = JSON.stringify([...userSel].sort()) === JSON.stringify([...q.correctAnswers].sort());
                points_awarded = is_correct ? 1 : 0;
            }
            return {
                question: q.id,
                test: q.test_id,
                session: currentSessionId,
                is_correct,
                points_awarded,
                time_spent_secs: questionTimes[q.id] || 0,
                difficulty_rating: difficultyRatings[q.id] || null,
            };
        });

        const totalMaxPoints = currentQuestions.reduce((sum, q) => sum + (q.maxPoints || 1), 0);
        const correctCount = attempts.filter(a => a.is_correct).length;

        try {
            await completeSession(currentSessionId, {
                total_questions: currentQuestions.length,
                correct_count: correctCount,
                score_achieved: score,
                score_possible: totalMaxPoints,
            });
            await submitAttempts(attempts);
        } catch (e) {
            console.error('Failed to finalize session:', e);
        }
    },

    fetchStats: async () => {
        set({ statsLoading: true });
        try {
            const response = await getUserStats();
            set({ userStats: response.data, statsLoading: false });
        } catch (e) {
            console.error('Failed to fetch stats:', e);
            set({ statsLoading: false });
        }
    },

    goToStats: () => set({ view: 'stats' }),

    // Spaced repetition actions
    rateDifficulty: (questionId, rating) => set(state => ({
        difficultyRatings: { ...state.difficultyRatings, [questionId]: rating },
    })),

    fetchStudyQueueCount: async () => {
        if (!get().user) return;
        try {
            const res = await getStudyQueue(20);
            set({ studyQueueCount: res.data.count });
        } catch (e) {
            // Silently ignore — count badge is non-critical
        }
    },

    startStudyMode: async () => {
        set({ isLoading: true, error: null, score: 0, currentQuestionIndex: 0, userAnswers: {}, questionTimes: {}, difficultyRatings: {}, currentSessionId: null });
        try {
            const res = await getStudyQueue(20);
            const questions = res.data.questions;
            if (!questions || questions.length === 0) {
                set({ isLoading: false, error: { message: 'No questions in your study queue right now.', code: 'EMPTY_QUEUE' } });
                return;
            }
            set({
                currentQuestions: questions,
                isLoading: false,
                view: 'test',
                testStartTime: new Date(),
                isTimerRunning: true,
                questionStartTime: new Date(),
            });
            if (get().user) {
                try {
                    const sessionRes = await startSession({ is_study_mode: true });
                    set({ currentSessionId: sessionRes.data.session_id });
                } catch (e) {
                    console.error('Failed to start study session:', e);
                }
            }
        } catch (e) {
            console.error('Failed to load study queue:', e);
            set({ isLoading: false, error: e });
        }
    },

    toggleTheme: () => set((state) => {
        const newTheme = state.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', newTheme);
        return { theme: newTheme };
    }),

    reviewAnswers: () => set({ view: 'review' }),

    backToResults: () => set({ view: 'results' }),

    // Auth actions
    initAuth: () => {
        const token = localStorage.getItem('auth_token');
        const username = localStorage.getItem('auth_username');
        if (token && username) {
            set({ authToken: token, user: { username } });
        }
    },

    login: async (credentials) => {
        set({ isAuthLoading: true, authError: null });
        try {
            const response = await loginUser(credentials);
            const { token, username } = response.data;
            localStorage.setItem('auth_token', token);
            localStorage.setItem('auth_username', username);
            set({ authToken: token, user: { username }, isAuthLoading: false, view: 'home' });
        } catch (error) {
            set({ authError: error, isAuthLoading: false });
        }
    },

    register: async (credentials) => {
        set({ isAuthLoading: true, authError: null });
        try {
            const response = await registerUser(credentials);
            const { token, username } = response.data;
            localStorage.setItem('auth_token', token);
            localStorage.setItem('auth_username', username);
            set({ authToken: token, user: { username }, isAuthLoading: false, view: 'home' });
        } catch (error) {
            set({ authError: error, isAuthLoading: false });
        }
    },

    logout: async () => {
        try {
            await logoutUser();
        } catch (_) {
            // Ignore errors — clear local state regardless
        }
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_username');
        set({ authToken: null, user: null });
    },

    goToLogin: () => set({ authError: null, view: 'login' }),
    goToRegister: () => set({ authError: null, view: 'register' }),
}));

export default useTestStore;
