import { create } from 'zustand';
import { getAvailableTests, getQuestions, checkOpenAnswer as checkOpenAnswerApi } from '../services/api';

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

    isCheckingAnswer: false,
    lastAnswerFeedback: null,
    openQuestionResults: {},

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
        set({ isLoading: true, error: null, view: 'test', score: 0, currentQuestionIndex: 0, userAnswers: {} });
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
                isTimerRunning: true, // Start timer when questions are loaded
                questionStartTime: new Date(), // Mark start of first question
            });
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
        const { currentQuestionIndex, currentQuestions, userAnswers, questionStartTime, totalTimeSpent } = get();
        const question = currentQuestions[currentQuestionIndex];
        const userSelection = userAnswers[question.id] || [];
        const isCorrect = JSON.stringify(userSelection.sort()) === JSON.stringify(question.correctAnswers.sort());
        if(isCorrect) set(state => ({ score: state.score + 1 }));
        
        // Accumulate time and pause timer
        if (questionStartTime) {
            const timeElapsed = Math.floor((new Date() - new Date(questionStartTime)) / 1000);
            set(state => ({
                totalTimeSpent: state.totalTimeSpent + timeElapsed,
                isTimerRunning: false, // Pause timer
            }));
        }
    },
    
    checkOpenAnswer: async (userAnswer) => {
        const { currentQuestionIndex, currentQuestions, questionStartTime, totalTimeSpent } = get();
        const question = currentQuestions[currentQuestionIndex];
        
        // Pause timer and accumulate time before checking answer
        if (questionStartTime) {
            const timeElapsed = Math.floor((new Date() - new Date(questionStartTime)) / 1000);
            set(state => ({
                totalTimeSpent: state.totalTimeSpent + timeElapsed,
                isTimerRunning: false, // Pause timer
            }));
        }

        set({ isCheckingAnswer: true, lastAnswerFeedback: null, error: null });

        try {
            const payload = {
                // POPRAWKA: Używamy 'questionText' zgodnie z tym, co wysyła backend
                questionText: question.questionText,
                userAnswer: userAnswer,
                gradingCriteria: question.gradingCriteria,
                maxPoints: question.maxPoints
            };
            const response = await checkOpenAnswerApi(payload);
            
            // KLUCZOWA POPRAWKA: Odczytujemy 'score' z API i mapujemy na 'points_awarded'
            const { score, feedback } = response.data;
            
            set(state => ({
                // Aktualizujemy ogólny wynik testu
                score: state.score + score,
                openQuestionResults: {
                    ...state.openQuestionResults,
                    [question.id]: {
                        userAnswer: userAnswer,
                        points_awarded: score,
                        feedback: feedback,
                        maxPoints: question.maxPoints
                    }
                },
                // Zapisujemy feedback do wyświetlenia na ekranie
                lastAnswerFeedback: { 
                    points_awarded: score, // Zapisujemy pod kluczem, którego oczekuje komponent
                    feedback: feedback, 
                    maxPoints: question.maxPoints 
                },
                isCheckingAnswer: false,
            }));

        } catch (error) {
            console.error("Błąd podczas sprawdzania odpowiedzi:", error);
            set({
                error: error,
                isCheckingAnswer: false,
            });
        }
    },

    nextQuestion: () => set((state) => {
        // Calculate time spent on the current question before moving to the next
        // This case handles moving to the next question after viewing feedback for open-ended questions
        // or if the user clicks "Dalej" without confirming a closed question (though confirmAnswer handles closed questions)
        if (state.questionStartTime && state.isTimerRunning) {
            const timeElapsed = Math.floor((new Date() - new Date(state.questionStartTime)) / 1000);
            state.totalTimeSpent += timeElapsed;
        }

        set({ lastAnswerFeedback: null, error: null });
        if (state.currentQuestionIndex + 1 < state.currentQuestions.length) {
            return {
                currentQuestionIndex: state.currentQuestionIndex + 1,
                questionStartTime: new Date(), // Reset start time for the new question
                isTimerRunning: true, // Resume timer for the new question
            };
        }
        return { view: 'results', testEndTime: new Date() };
    }),

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
        lastAnswerFeedback: null,
        openQuestionResults: {},
        isTimerRunning: false, // Reset timer state
        questionStartTime: null, // Reset question start time
        totalTimeSpent: 0, // Reset total time spent
    }),

    toggleTheme: () => set((state) => {
        const newTheme = state.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', newTheme);
        return { theme: newTheme };
    }),
    
    reviewAnswers: () => set({ view: 'review' }),
    
    backToResults: () => set({ view: 'results' }),
}));

export default useTestStore;
