import React, { useEffect, useMemo, useState } from 'react';
import useTestStore from '../store/testStore';
import { motion, AnimatePresence } from 'framer-motion';

// --- Komponent Modala ---
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
        resetTest
    } = useTestStore();

    // Lokalny stan dla pola input i jego walidacji
    const [numQuestionsInput, setNumQuestionsInput] = useState(numQuestionsConfig.toString());
    const [inputError, setInputError] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);

    const [expandedCategory, setExpandedCategory] = useState(null);

    useEffect(() => { fetchAvailableTests(); }, [fetchAvailableTests]);

    // Grupujemy testy i obliczamy sumę pytań dla każdej kategorii
    const testsByCategory = useMemo(() => {
        return availableTests.reduce((acc, test) => {
            const { category } = test;
            if (!acc[category]) {
                acc[category] = { tests: [], totalQuestions: 0 };
            }
            acc[category].tests.push(test);
            acc[category].totalQuestions += test.question_count;
            return acc;
        }, {});
    }, [availableTests]);

    // Obliczamy sumę dostępnych pytań na podstawie wybranych kategorii
    const totalAvailableQuestions = useMemo(() => {
        if (selectedCategories.length === 0) return 0;
        return availableTests
            .filter(test => selectedCategories.includes(test.test_id))
            .reduce((sum, test) => sum + test.question_count, 0);
    }, [selectedCategories, availableTests]);


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

    // Logika walidacji i aktualizacji liczby pytań
    const handleNumQuestionsChange = (e) => {
        const value = e.target.value;
        setNumQuestionsInput(value); // Pozwól na swobodne wpisywanie

        if (value === '') {
            setInputError('Pole nie może być puste.');
            return;
        }
        
        const num = parseInt(value, 10);
        if (isNaN(num) || num <= 0) {
            setInputError('Wprowadź liczbę większą od zera.');
        } else {
            setInputError('');
            setConfig(num, timerEnabled); // Aktualizuj stan globalny tylko, gdy wartość jest poprawna
        }
    };
    
    // Logika przycisku "Rozpocznij Test"
    const handleStartClick = () => {
        if (inputError || numQuestionsInput === '') {
            // Nie rób nic, jeśli jest błąd walidacji
            return;
        }

        const requestedCount = parseInt(numQuestionsInput, 10);

        if (requestedCount > totalAvailableQuestions) {
            setIsModalOpen(true); // Pokaż modal
        } else {
            startTest(); // Rozpocznij test normalnie
        }
    };
    
    // Logika potwierdzenia w modalu
    const handleConfirmStart = () => {
        // Ustaw liczbę pytań na maksymalną dostępną i rozpocznij test
        setConfig(totalAvailableQuestions, timerEnabled);
        startTest();
        setIsModalOpen(false);
    };

    const isStartButtonDisabled = isLoading || selectedCategories.length === 0 || !!inputError;

    return (
        <>
            <ConfirmationModal 
                isOpen={isModalOpen}
                availableCount={totalAvailableQuestions}
                requestedCount={parseInt(numQuestionsInput, 10)}
                onConfirm={handleConfirmStart}
                onCancel={() => setIsModalOpen(false)}
            />
            <motion.div 
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
                        {Object.entries(testsByCategory).map(([category, { tests, totalQuestions }]) => {
                            const allTestIds = tests.map(t => t.test_id);
                            const areAllSelected = allTestIds.every(id => selectedCategories.includes(id));

                            return (
                                <div key={category} className="bg-gray-100 dark:bg-option-bg border border-gray-300 dark:border-card-border rounded-lg transition-all duration-300 hover:border-brand-primary">
                                    <button 
                                        onClick={() => handleCategoryClick(category)} 
                                        className="w-full flex justify-between items-center p-5 font-bold text-xl text-gray-800 dark:text-white rounded-t-lg"
                                    >
                                        <span>{category} <span className="text-sm font-normal text-gray-500 dark:text-gray-400">({totalQuestions} pytań)</span></span>
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
                                                            <span className="ml-3 text-gray-700 dark:text-gray-200">{test.scope} ({test.version}) <span className="text-xs text-gray-500 dark:text-gray-400">[{test.question_count}]</span></span>
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
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Ustawienia</h2>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-6 space-y-4 sm:space-y-0">
                        <div className="flex-1">
                            <label htmlFor="num-questions" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Liczba pytań (dostępnych: {totalAvailableQuestions})
                            </label>
                            <input 
                                type="text" 
                                id="num-questions" 
                                className={`w-full p-2 bg-gray-50 dark:bg-gray-900 border rounded-md text-gray-800 dark:text-white focus:ring-brand-primary focus:border-brand-primary ${inputError ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}`}
                                value={numQuestionsInput} 
                                onChange={handleNumQuestionsChange}
                            />
                            {inputError && <p className="text-red-500 text-xs mt-1">{inputError}</p>}
                        </div>
                        <div className="flex items-center pt-6">
                            <input 
                                id="timer-enabled" 
                                type="checkbox" 
                                className="h-5 w-5 rounded bg-gray-300 dark:bg-gray-700 border-gray-400 dark:border-gray-600 text-brand-primary focus:ring-brand-primary"
                                checked={timerEnabled} 
                                onChange={(e) => setConfig(numQuestionsConfig, e.target.checked)} 
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
