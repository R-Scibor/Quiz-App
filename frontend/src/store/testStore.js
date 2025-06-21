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
            set({ error: 'Nie udało się pobrać listy testów.', isLoading: false });
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
            set({ error: 'Wybierz przynajmniej jedną kategorię.' });
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
            });
        } catch (error) {
            set({ error: 'Nie udało się pobrać pytań do testu.', isLoading: false, view: 'setup' });
        }
    },
    
    submitAnswer: (questionId, answer) => set((state) => ({
        userAnswers: { ...state.userAnswers, [questionId]: answer },
    })),

    confirmAnswer: () => {
        const { currentQuestionIndex, currentQuestions, userAnswers } = get();
        const question = currentQuestions[currentQuestionIndex];
        const userSelection = userAnswers[question.id] || [];
        const isCorrect = JSON.stringify(userSelection.sort()) === JSON.stringify(question.correctAnswers.sort());
        if(isCorrect) set(state => ({ score: state.score + 1 }));
    },
    
    checkOpenAnswer: async (userAnswer) => {
        const { currentQuestionIndex, currentQuestions } = get();
        const question = currentQuestions[currentQuestionIndex];
        
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
                error: 'Wystąpił błąd podczas sprawdzania odpowiedzi. Spróbuj ponownie.',
                isCheckingAnswer: false,
            });
        }
    },

    nextQuestion: () => set((state) => {
        set({ lastAnswerFeedback: null, error: null }); 
        if (state.currentQuestionIndex + 1 < state.currentQuestions.length) {
            return { currentQuestionIndex: state.currentQuestionIndex + 1 };
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
