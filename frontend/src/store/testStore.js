import { create } from 'zustand';
import { getAvailableTests, getQuestions, checkOpenAnswer as checkOpenAnswerApi, getTaskResult as getTaskResultApi, registerUser, loginUser, logoutUser, startSession, completeSession, submitAttempts, getUserStats, getTestStats, getStudyQueue, getStudyStats } from '../services/api';

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
    activePolls: {}, // { [taskId]: intervalId } — persists polling across view/component changes

    // Auth state
    user: null,
    authToken: null,
    isAuthLoading: false,
    authError: null,

    // Session / stats state
    currentSessionId: null,
    userStats: null,
    testStats: null,
    statsLoading: false,

    // Spaced repetition state
    difficultyRatings: {},   // { questionId: 'easy' | 'normal' | 'hard' }
    studyQueueCount: null,   // number of due questions for home page badge
    studySetupData: null,    // { due_count, struggling_count, new_count, mastered_count, total_queued, studied_tests }
    studyNumQuestions: 20,   // persisted session length preference
    studySelectedTestIds: null, // null = all; array of UUIDs = filtered

    // Actions
    goToSetup: () => set({ view: 'setup' }),

    fetchAvailableTests: async () => {
        set({ isLoading: true, error: null });
        try {
            const response = await getAvailableTests();
            const tests = response.data.map(test => ({ ...test, question_counts: test.question_counts || { closed: 0, open: 0, total: 0 } }));
            set({ availableTests: tests, isLoading: false });
        } catch (error) {
            console.error("Failed to fetch tests:", error);
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
            set({ error: { message: 'Select at least one category.', code: 'VALIDATION_ERROR' } });
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
            console.error("Failed to fetch questions:", error);
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
    
    checkOpenAnswer: async (userAnswer, forceAI = false) => {
        const { currentQuestionIndex, currentQuestions, questionStartTime, checkingQuestionId } = get();
        const question = currentQuestions[currentQuestionIndex];

        if (checkingQuestionId === question.id) return { task_id: null };

        // Only record time on the first (non-forced) submission
        if (!forceAI && questionStartTime) {
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
            maxPoints: question.maxPoints,
            questionType: question.type,
            forceAI: forceAI,
        };

        const response = await checkOpenAnswerApi(payload);
        return response.data;
    },

    getTaskResult: async (taskId) => {
        const response = await getTaskResultApi(taskId);
        return response.data; // Returns { status, data }
    },

    startPolling: (taskId, questionId) => {
        let retries = 0;
        const MAX_RETRIES = 60; // 60 × 2s = 120s timeout
        const interval = setInterval(async () => {
            const clearPoll = () => {
                clearInterval(interval);
                set(state => {
                    const polls = { ...state.activePolls };
                    delete polls[taskId];
                    return { activePolls: polls };
                });
            };
            if (retries >= MAX_RETRIES) {
                clearPoll();
                get().setError({ message: 'AI grading timed out. Please try again.' });
                return;
            }
            retries++;
            try {
                const resultResponse = await getTaskResultApi(taskId);
                const data = resultResponse.data;
                if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
                    clearPoll();
                    if (data.status === 'SUCCESS') {
                        get().setLastAnswerFeedback(data.data, questionId);
                    } else {
                        get().setError({ message: data.data || 'An error occurred while processing the task.' });
                    }
                }
            } catch (error) {
                clearPoll();
                get().setError({ message: error.message || 'Error checking task result.' });
            }
        }, 2000);
        set(state => ({ activePolls: { ...state.activePolls, [taskId]: interval } }));
    },

    regradeQuestion: async (questionId) => {
        const { currentQuestions, openQuestionResults } = get();
        const question = currentQuestions.find(q => q.id === questionId);
        const userAnswer = openQuestionResults[questionId]?.userAnswer;
        if (!question || !userAnswer) return null;
        set({ checkingQuestionId: questionId, error: null });
        const response = await checkOpenAnswerApi({
            questionText: question.questionText,
            userAnswer,
            gradingCriteria: question.gradingCriteria,
            maxPoints: question.maxPoints,
            questionType: question.type,
            forceAI: true,
        });
        return response.data; // { task_id }
    },

    setLastAnswerFeedback: (feedbackData, questionId) => {
        const { score, feedback, grading_method } = feedbackData;
        const { currentQuestions } = get();
        const question = currentQuestions.find(q => q.id === questionId);

        if (!question) return;

        set(state => {
            // Subtract any previously awarded points for this question (re-grading support)
            const oldPoints = state.openQuestionResults[questionId]?.points_awarded ?? 0;
            return {
            score: state.score - oldPoints + score,
            openQuestionResults: {
                ...state.openQuestionResults,
                [questionId]: {
                    ...state.openQuestionResults[questionId],
                    points_awarded: score,
                    feedback: feedback,
                    maxPoints: question.maxPoints,
                    grading_method: grading_method ?? null,
                }
            },
            // Clear the checking state only if it matches the question that just finished
            checkingQuestionId: state.checkingQuestionId === questionId
                ? null
                : state.checkingQuestionId,
            };
        });
    },

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

    resetTest: () => {
        const { activePolls } = get();
        Object.values(activePolls).forEach(clearInterval);
        set({
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
            activePolls: {},
            isTimerRunning: false,
            questionStartTime: null,
            totalTimeSpent: 0,
            questionTimes: {},
            currentSessionId: null,
            difficultyRatings: {},
            studySelectedTestIds: null,
        });
    },

    retryTest: () => {
        const { activePolls } = get();
        Object.values(activePolls).forEach(clearInterval);
        set({
            view: 'setup',
            currentQuestions: [],
            currentQuestionIndex: 0,
            userAnswers: {},
            score: 0,
            testStartTime: null,
            testEndTime: null,
            error: null,
            openQuestionResults: {},
            checkingQuestionId: null,
            activePolls: {},
            isTimerRunning: false,
            questionStartTime: null,
            totalTimeSpent: 0,
            questionTimes: {},
            currentSessionId: null,
            difficultyRatings: {},
            studySelectedTestIds: null,
            // selectedCategories, numQuestionsConfig, timerEnabled, questionMode are preserved
        });
    },

    _finalizeSession: async () => {
        const { currentSessionId, user, currentQuestions, userAnswers, openQuestionResults, score, questionTimes, difficultyRatings } = get();
        if (!currentSessionId || !user) return;

        const attempts = currentQuestions.map(q => {
            let is_correct, points_awarded;
            if (q.type.startsWith('open-')) {
                const result = openQuestionResults[q.id];
                points_awarded = result?.points_awarded ?? 0;
                is_correct = points_awarded >= q.maxPoints * 0.66;
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
        } catch (e) {
            console.error('Failed to complete session:', e);
        }
        try {
            await submitAttempts(attempts);
        } catch (e) {
            console.error('Failed to submit attempts:', e);
        }
    },

    fetchStats: async () => {
        set({ statsLoading: true });
        try {
            const [statsRes, testStatsRes] = await Promise.all([getUserStats(), getTestStats()]);
            set({ userStats: statsRes.data, testStats: testStatsRes.data, statsLoading: false });
        } catch (e) {
            console.error('Failed to fetch stats:', e);
            set({ statsLoading: false });
        }
    },

    goToHome: () => set({ view: 'home' }),
    goToStats: () => set({ view: 'stats' }),

    // Spaced repetition actions
    rateDifficulty: (questionId, rating) => set(state => ({
        difficultyRatings: { ...state.difficultyRatings, [questionId]: rating },
    })),

    fetchStudyStats: async () => {
        if (!get().user) return;
        try {
            const res = await getStudyStats();
            set({ studyQueueCount: res.data.total_queued, studySetupData: res.data });
        } catch {
            // Silently ignore — count badge is non-critical
        }
    },

    goToStudySetup: async () => {
        if (!get().studySetupData) await get().fetchStudyStats();
        set({ view: 'study-setup' });
    },

    setStudyConfig: (numQuestions, testIds) => set({
        studyNumQuestions: numQuestions,
        studySelectedTestIds: testIds,
    }),

    startStudyMode: async () => {
        const { studyNumQuestions, studySelectedTestIds } = get();
        set({ isLoading: true, error: null, score: 0, currentQuestionIndex: 0, userAnswers: {}, questionTimes: {}, difficultyRatings: {}, currentSessionId: null });
        try {
            const res = await getStudyQueue(studyNumQuestions, studySelectedTestIds);
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
        } catch {
            // Ignore errors — clear local state regardless
        }
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_username');
        set({ authToken: null, user: null });
    },

    handleUnauthorized: () => {
        const { view, activePolls } = get();
        Object.values(activePolls).forEach(clearInterval);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_username');
        const midQuiz = view === 'test' || view === 'results' || view === 'review';
        set({
            authToken: null,
            user: null,
            currentSessionId: null,
            checkingQuestionId: null,
            activePolls: {},
            view: 'login',
            authError: {
                code: 'SESSION_EXPIRED',
                message: midQuiz
                    ? 'Your session expired. Progress for this quiz was not saved. Please log in again.'
                    : 'Your session expired. Please log in again.',
            },
        });
    },

    goToLogin: () => set({ authError: null, view: 'login' }),
    goToRegister: () => set({ authError: null, view: 'register' }),
}));

export default useTestStore;
