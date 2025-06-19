import React, { useEffect, useMemo, useState } from 'react';
import useTestStore from '../store/testStore';
import { motion, AnimatePresence } from 'framer-motion';

// --- Komponent Modala Potwierdzenia ---
const ConfirmationModal = ({ isOpen, availableCount, requestedCount, onConfirm, onCancel }) => {
    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    className="main-card bg-white dark:bg-card-bg w-full max-w-md p-8 rounded-2xl"
                >
                    <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Uwaga</h2>
                    <p className="text-gray-600 dark:text-gray-300 my-4">
                        Wybrano {requestedCount} pytań, ale w zaznaczonych kategoriach dostępnych jest tylko {availableCount}.
                    </p>
                    <p className="text-gray-600 dark:text-gray-300 font-semibold">
                        Czy chcesz rozpocząć test z {availableCount} pytaniami?
                    </p>
                    <div className="flex justify-end gap-4 mt-8">
                        <button onClick={onCancel} className="btn-secondary py-2 px-6">Anuluj</button>
                        <button onClick={onConfirm} className="btn-primary py-2 px-6">Rozpocznij</button>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

// --- Komponent Modala z Ostrzeżeniem o AI ---
const LlmWarningModal = ({ isOpen, onConfirm, onCancel }) => {
    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    className="main-card bg-white dark:bg-card-bg w-full max-w-md p-8 rounded-2xl"
                >
                    <h2 className="text-2xl font-bold text-brand-primary">Uwaga</h2>
                    <div className="text-gray-600 dark:text-gray-300 my-4 space-y-3">
                        <p>
                            Pytania otwarte są oceniane przez LLM (Duży Model Językowy), przez co w niektórych przypadkach mogą być niesłusznie ocenione.
                        </p>
                        <p className="font-semibold">
                            Bajabongo Entertainment nie ma wpływu na odpowiedzi LLM.
                        </p>
                        <p>
                            Czy chcesz kontynuować z pytaniami otwartymi?
                        </p>
                    </div>
                    <div className="flex justify-end gap-4 mt-8">
                        <button onClick={onCancel} className="btn-secondary py-2 px-6">Anuluj</button>
                        <button onClick={onConfirm} className="btn-primary py-2 px-6">Kontynuuj</button>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

const ChevronIcon = ({ expanded }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}>
        <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
);

const TestSetupPage = () => {
    const { 
        fetchAvailableTests, 
        availableTests,
        isLoading, 
        error, 
        selectedCategories, 
        toggleCategory, 
        numQuestionsConfig, 
        timerEnabled, 
        setConfig, 
        startTest,
        resetTest,
        questionMode,
        setQuestionMode
    } = useTestStore();

    const [numQuestionsInput, setNumQuestionsInput] = useState(numQuestionsConfig.toString());
    const [inputError, setInputError] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [expandedCategory, setExpandedCategory] = useState(null);

    // Stany do obsługi modala z ostrzeżeniem
    const [isLlmWarningModalOpen, setIsLlmWarningModalOpen] = useState(false);
    const [pendingQuestionMode, setPendingQuestionMode] = useState(null);


    useEffect(() => { 
        fetchAvailableTests(); 
    }, [fetchAvailableTests]);

    const testsByCategory = useMemo(() => {
        return availableTests.reduce((acc, test) => {
            const { category } = test;
            if (!acc[category]) {
                acc[category] = { tests: [], question_counts: { total: 0, closed: 0, open: 0 } };
            }
            acc[category].tests.push(test);
            acc[category].question_counts.total += test.question_counts.total;
            acc[category].question_counts.closed += test.question_counts.closed;
            acc[category].question_counts.open += test.question_counts.open;
            return acc;
        }, {});
    }, [availableTests]);

    const totalAvailableQuestions = useMemo(() => {
        if (selectedCategories.length === 0) return 0;
        
        return availableTests
            .filter(test => selectedCategories.includes(test.test_id))
            .reduce((sum, test) => {
                const counts = test.question_counts;
                if (questionMode === 'closed') {
                    return sum + counts.closed;
                } else if (questionMode === 'open') {
                    return sum + counts.open;
                }
                return sum + counts.total;
            }, 0);
    }, [selectedCategories, availableTests, questionMode]);

    useEffect(() => {
        if (totalAvailableQuestions > 0) {
            const currentNum = parseInt(numQuestionsInput, 10);
            if (isNaN(currentNum) || currentNum > totalAvailableQuestions) {
                const newNum = Math.min(10, totalAvailableQuestions);
                setNumQuestionsInput(newNum.toString());
                setConfig(newNum, timerEnabled);
                setInputError('');
            }
        } else {
             const newNum = Math.min(10, totalAvailableQuestions);
             setNumQuestionsInput(newNum.toString());
             setConfig(newNum, timerEnabled);
        }
    }, [totalAvailableQuestions, selectedCategories, questionMode]);

    const handleCategoryClick = (category) => {
        setExpandedCategory(prev => (prev === category ? null : category));
    };

    const handleSelectAll = (tests, areAllSelected) => {
        tests.forEach(test => {
            const isCurrentlySelected = selectedCategories.includes(test.test_id);
            if (areAllSelected && isCurrentlySelected) {
                toggleCategory(test.test_id);
            } else if (!areAllSelected && !isCurrentlySelected) {
                toggleCategory(test.test_id);
            }
        });
    };

    const handleNumQuestionsChange = (e) => {
        const value = e.target.value;
        setNumQuestionsInput(value); 

        if (value === '') {
            setInputError('Pole nie może być puste.');
            return;
        }
        
        const num = parseInt(value, 10);
        if (isNaN(num) || num <= 0) {
            setInputError('Wprowadź liczbę większą od zera.');
        } else if (num > totalAvailableQuestions) {
            setInputError(`Maksymalna liczba pytań dla tego trybu to ${totalAvailableQuestions}.`);
        } else {
            setInputError('');
            setConfig(num, timerEnabled);
        }
    };
    
    // Obsługa zmiany trybu pytań z modalem
    const handleModeChange = (e) => {
        const newMode = e.target.value;
        if (newMode === 'open' || newMode === 'mixed') {
            setPendingQuestionMode(newMode);
            setIsLlmWarningModalOpen(true);
        } else {
            setQuestionMode(newMode);
        }
    };

    const handleConfirmLlmWarning = () => {
        if (pendingQuestionMode) {
            setQuestionMode(pendingQuestionMode);
        }
        setIsLlmWarningModalOpen(false);
        setPendingQuestionMode(null);
    };

    const handleCancelLlmWarning = () => {
        setIsLlmWarningModalOpen(false);
        setPendingQuestionMode(null);
    };


    const handleStartClick = () => {
        if (inputError || numQuestionsInput === '' || totalAvailableQuestions === 0) {
            return;
        }

        const requestedCount = parseInt(numQuestionsInput, 10);
        
        if (requestedCount > totalAvailableQuestions) {
            setIsModalOpen(true);
        } else {
            startTest();
        }
    };
    
    const handleConfirmStart = () => {
        setConfig(totalAvailableQuestions, timerEnabled);
        startTest();
        setIsModalOpen(false);
    };

    const isStartButtonDisabled = isLoading || selectedCategories.length === 0 || !!inputError || totalAvailableQuestions === 0;

    return (
        <>
            <ConfirmationModal 
                isOpen={isModalOpen}
                availableCount={totalAvailableQuestions}
                requestedCount={parseInt(numQuestionsInput, 10)}
                onConfirm={handleConfirmStart}
                onCancel={() => setIsModalOpen(false)}
            />
            <LlmWarningModal
                isOpen={isLlmWarningModalOpen}
                onConfirm={handleConfirmLlmWarning}
                onCancel={handleCancelLlmWarning}
            />
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto p-8 md:p-12 text-center"
            >
                <div className="w-full flex justify-start mb-6">
                    <motion.button 
                        onClick={resetTest}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 hover:text-brand-primary dark:hover:text-brand-primary transition-colors"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                        Wróć do strony głównej
                    </motion.button>
                </div>
                
                <h1 className="text-4xl md:text-5xl font-bold text-gray-800 dark:text-white mb-2">Wybierz Kategorię</h1>
                <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">Sprawdź swoją wiedzę w różnych dziedzinach.</p>
                
                {error && <p className="text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/50 p-3 rounded-md mb-6">{error}</p>}
                
                <div className="mb-8 text-left">
                    {isLoading && availableTests.length === 0 && <p className="text-center text-gray-600 dark:text-gray-400">Ładowanie listy testów...</p>}
                    
                    <div className="space-y-4">
                        {Object.entries(testsByCategory).map(([category, { tests, question_counts }]) => {
                            const allTestIds = tests.map(t => t.test_id);
                            const areAllSelected = allTestIds.every(id => selectedCategories.includes(id));

                            return (
                                <div key={category} className="bg-gray-100 dark:bg-option-bg border border-gray-300 dark:border-card-border rounded-lg transition-all duration-300 hover:border-brand-primary">
                                    <button 
                                        onClick={() => handleCategoryClick(category)} 
                                        className="w-full flex justify-between items-center p-5 font-bold text-xl text-gray-800 dark:text-white rounded-t-lg"
                                    >
                                        <div className='flex flex-col items-start'>
                                          <span>{category}</span>
                                          <span className="text-xs font-normal text-gray-500 dark:text-gray-400">
                                            Całkowita: {question_counts.total}, Zamknięte: {question_counts.closed}, Otwarte: {question_counts.open}
                                          </span>
                                        </div>
                                        <ChevronIcon expanded={expandedCategory === category} />
                                    </button>
                                    
                                    <div className={`grid transition-[grid-template-rows] duration-300 ease-in-out ${expandedCategory === category ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
                                        <div className="overflow-hidden">
                                            <div className="p-5 border-t border-gray-300 dark:border-card-border space-y-4">
                                                <label className="flex items-center w-full cursor-pointer p-3 rounded-md bg-gray-200 dark:bg-black/20 hover:bg-gray-300 dark:hover:bg-black/40 transition-colors">
                                                    <input
                                                        type="checkbox"
                                                        checked={areAllSelected}
                                                        onChange={() => handleSelectAll(tests, areAllSelected)}
                                                        className="h-5 w-5 rounded bg-gray-300 dark:bg-gray-700 border-gray-400 dark:border-gray-600 text-brand-primary focus:ring-brand-primary"
                                                    />
                                                    <span className="ml-3 font-semibold text-gray-700 dark:text-gray-200">Zaznacz całą kategorię</span>
                                                </label>

                                                <div className="space-y-3 pl-3 border-l-2 border-gray-300 dark:border-gray-700/50">
                                                    {tests.map(test => (
                                                        <label key={test.test_id} className="flex items-center cursor-pointer p-2 rounded-md hover:bg-gray-200 dark:hover:bg-white/5 transition-colors">
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedCategories.includes(test.test_id)}
                                                                onChange={() => toggleCategory(test.test_id)}
                                                                className="h-5 w-5 rounded bg-gray-300 dark:bg-gray-700 border-gray-400 dark:border-gray-600 text-brand-primary focus:ring-brand-primary"
                                                            />
                                                            <span className="ml-3 text-gray-700 dark:text-gray-200">
                                                                {test.scope} ({test.version})
                                                                <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                                                                    [Z: {test.question_counts.closed}, O: {test.question_counts.open}]
                                                                </span>
                                                            </span>
                                                        </label>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <div className="mb-8 text-left p-6 bg-gray-200 dark:bg-black/20 rounded-lg border border-solid border-gray-300 dark:border-gray-700">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Tryb Pytań</h2>
                    <div className="flex flex-col sm:flex-row justify-around gap-4">
                        {['closed', 'open', 'mixed'].map((mode) => (
                            <label key={mode} className="flex items-center cursor-pointer">
                                <input
                                    type="radio"
                                    name="questionMode"
                                    value={mode}
                                    checked={questionMode === mode}
                                    onChange={handleModeChange}
                                    className="h-5 w-5 text-brand-primary focus:ring-brand-primary"
                                />
                                <span className="ml-3 text-gray-700 dark:text-gray-200 capitalize">
                                    {mode === 'mixed' ? 'Mieszane' : mode === 'closed' ? 'Zamknięte' : 'Otwarte'}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>

                <div className="mb-8 text-left p-6 bg-gray-200 dark:bg-black/20 rounded-lg border border-solid border-gray-300 dark:border-gray-700">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Ustawienia</h2>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-6 space-y-4 sm:space-y-0">
                        <div className="flex-1">
                            <label htmlFor="num-questions" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Liczba pytań (dostępnych: {totalAvailableQuestions})
                            </label>
                            <input 
                                type="number" 
                                id="num-questions" 
                                className={`w-full p-2 bg-gray-50 dark:bg-gray-900 border rounded-md text-gray-800 dark:text-white focus:ring-brand-primary focus:border-brand-primary ${inputError ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`}
                                value={numQuestionsInput} 
                                onChange={handleNumQuestionsChange}
                                max={totalAvailableQuestions}
                                min="1"
                            />
                            {inputError && <p className="text-red-500 text-xs mt-1">{inputError}</p>}
                        </div>
                        <div className="flex items-center pt-6">
                            <input 
                                id="timer-enabled" 
                                type="checkbox" 
                                className="h-5 w-5 rounded bg-gray-300 dark:bg-gray-700 border-gray-400 dark:border-gray-600 text-brand-primary focus:ring-brand-primary"
                                checked={timerEnabled} 
                                onChange={(e) => setConfig(parseInt(numQuestionsInput, 10), e.target.checked)} 
                            />
                            <label htmlFor="timer-enabled" className="ml-3 block font-medium text-gray-700 dark:text-gray-300">Włącz licznik</label>
                        </div>
                    </div>
                </div>

                <motion.button 
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleStartClick} 
                    disabled={isStartButtonDisabled} 
                    className="bg-brand-primary text-white font-bold py-3 px-10 rounded-full text-lg shadow-primary hover:bg-brand-primary-hover hover:shadow-primary-hover disabled:bg-gray-500 dark:disabled:bg-gray-700 disabled:shadow-none disabled:cursor-not-allowed transition-all duration-300 ease-in-out disabled:transform-none"
                >
                    {isLoading ? "Ładowanie..." : "Rozpocznij Test"}
                </motion.button>
            </motion.div>
        </>
    );
};
export default TestSetupPage;
