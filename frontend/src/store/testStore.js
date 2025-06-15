import { create } from 'zustand';
import { getAvailableTests, getQuestions } from '../services/api';

const initialTheme = localStorage.getItem('theme') || 'dark';

const useTestStore = create((set, get) => ({
    // ZMIANA: 'home' jest teraz domyślnym widokiem
    view: 'home',
    availableTests: [],
    selectedCategories: [],
    numQuestionsConfig: 10,
    timerEnabled: false,
    currentQuestions: [],
    currentQuestionIndex: 0,
    userAnswers: {},
    score: 0,
    testStartTime: null,
    testEndTime: null,
    isLoading: false,
    error: null,
    theme: initialTheme,
    
    // ZMIANA: Nowa akcja do nawigacji na stronę konfiguracji
    goToSetup: () => set({ view: 'setup' }),

    fetchAvailableTests: async () => {
        set({ isLoading: true, error: null });
        try {
            const response = await getAvailableTests();
            set({ availableTests: response.data, isLoading: false });
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
    setConfig: (num, timer) => set({ numQuestionsConfig: num, timerEnabled: timer }),
    startTest: async () => {
        const { numQuestionsConfig, selectedCategories } = get();
        if (selectedCategories.length === 0) {
            set({ error: 'Wybierz przynajmniej jedną kategorię.' });
            return;
        }
        set({ isLoading: true, error: null, view: 'test', score: 0, currentQuestionIndex: 0, userAnswers: {} });
        try {
            const response = await getQuestions({
                categories: selectedCategories.join(','),
                num_questions: numQuestionsConfig
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
    submitAnswer: (questionId, answerIndexes) => set((state) => ({
        userAnswers: { ...state.userAnswers, [questionId]: answerIndexes },
    })),
    confirmAnswer: () => {
        const { currentQuestionIndex, currentQuestions, userAnswers } = get();
        const question = currentQuestions[currentQuestionIndex];
        const userSelection = userAnswers[question.id] || [];
        const isCorrect = JSON.stringify(userSelection.sort()) === JSON.stringify(question.correctAnswers.sort());
        if(isCorrect) set(state => ({ score: state.score + 1 }));
    },
    nextQuestion: () => set((state) => {
        if (state.currentQuestionIndex + 1 < state.currentQuestions.length) {
            return { currentQuestionIndex: state.currentQuestionIndex + 1 };
        }
        return { view: 'results', testEndTime: new Date() };
    }),
    resetTest: () => set({
        // ZMIANA: Resetowanie przenosi teraz na stronę główną
        view: 'home', 
        selectedCategories: [], 
        currentQuestions: [],
        currentQuestionIndex: 0, 
        userAnswers: {}, 
        score: 0,
        testStartTime: null, 
        testEndTime: null, 
        error: null,
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
