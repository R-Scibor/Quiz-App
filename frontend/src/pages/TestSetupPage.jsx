import React, { useEffect, useMemo, useState } from 'react';
import useTestStore from '../store/testStore';
// ZMIANA: Importujemy motion
import { motion } from 'framer-motion';

const ChevronIcon = ({ expanded }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}>
        <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
);

// ZMIANA: Definiujemy warianty animacji dla listy
const listVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
};
  
const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
};

const TestSetupPage = () => {
    const { 
        availableTests, 
        fetchAvailableTests, 
        isLoading, 
        error, 
        selectedCategories, 
        toggleCategory, 
        numQuestionsConfig, 
        timerEnabled, 
        setConfig, 
        startTest 
    } = useTestStore();

    const [expandedCategory, setExpandedCategory] = useState(null);

    useEffect(() => { fetchAvailableTests(); }, [fetchAvailableTests]);

    const testsByCategory = useMemo(() => {
        return availableTests.reduce((acc, test) => {
            const { category } = test;
            if (!acc[category]) {
                acc[category] = [];
            }
            acc[category].push(test);
            return acc;
        }, {});
    }, [availableTests]);

    const handleCategoryClick = (category) => {
        setExpandedCategory(prev => (prev === category ? null : category));
    };

    const handleSelectAll = (tests, areAllSelected) => {
        tests.forEach(test => {
            const isCurrentlySelected = selectedCategories.includes(test.test_id);
            if (areAllSelected && isCurrentlySelected) {
                toggleCategory(test.test_id);
            }
            else if (!areAllSelected && !isCurrentlySelected) {
                toggleCategory(test.test_id);
            }
        });
    };
    
    const isStartButtonDisabled = isLoading || selectedCategories.length === 0;

    return (
        <motion.div 
            className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto p-8 md:p-12 text-center"
        >
            <h1 className="text-4xl md:text-5xl font-bold text-gray-800 dark:text-white mb-2">Wybierz Kategorię</h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">Sprawdź swoją wiedzę w różnych dziedzinach.</p>
            
            {error && <p className="text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/50 p-3 rounded-md mb-6">{error}</p>}
            
            <div className="mb-8 text-left">
                {isLoading && availableTests.length === 0 && <p className="text-center text-gray-600 dark:text-gray-400">Ładowanie listy testów...</p>}
                
                <motion.div 
                    className="space-y-4"
                    variants={listVariants}
                    initial="hidden"
                    animate="visible"
                >
                    {Object.entries(testsByCategory).map(([category, tests]) => {
                        const allTestIds = tests.map(t => t.test_id);
                        const selectedCount = allTestIds.filter(id => selectedCategories.includes(id)).length;
                        const areAllSelected = selectedCount === allTestIds.length;

                        return (
                            <motion.div key={category} variants={itemVariants} className="bg-gray-100 dark:bg-option-bg border border-gray-300 dark:border-card-border rounded-lg transition-all duration-300 hover:border-brand-primary">
                                <button 
                                    onClick={() => handleCategoryClick(category)} 
                                    className="w-full flex justify-between items-center p-5 font-bold text-xl text-gray-800 dark:text-white rounded-t-lg"
                                >
                                    <span>{category}</span>
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
                                                        <span className="ml-3 text-gray-700 dark:text-gray-200">{test.scope} ({test.version})</span>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </motion.div>
            </div>

            <div className="mb-8 text-left p-6 bg-gray-200 dark:bg-black/20 rounded-lg border border-solid border-gray-300 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Ustawienia</h2>
                <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-6 space-y-4 sm:space-y-0">
                    <div className="flex-1">
                        <label htmlFor="num-questions" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Liczba pytań</label>
                        <input 
                            type="number" 
                            id="num-questions" 
                            className="w-full p-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md text-gray-800 dark:text-white focus:ring-brand-primary focus:border-brand-primary" 
                            value={numQuestionsConfig} 
                            onChange={(e) => setConfig(parseInt(e.target.value, 10) || 1, timerEnabled)} 
                        />
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
                onClick={startTest} 
                disabled={isStartButtonDisabled} 
                className="bg-brand-primary text-white font-bold py-3 px-10 rounded-full text-lg shadow-primary hover:bg-brand-primary-hover hover:shadow-primary-hover disabled:bg-gray-500 dark:disabled:bg-gray-700 disabled:shadow-none disabled:cursor-not-allowed transition-all duration-300 ease-in-out disabled:transform-none"
            >
                {isLoading ? "Ładowanie..." : "Rozpocznij Test"}
            </motion.button>
        </motion.div>
    );
};
export default TestSetupPage;
