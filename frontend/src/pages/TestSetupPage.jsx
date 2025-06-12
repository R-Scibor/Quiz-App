import React, { useEffect, useMemo, useState } from 'react';
import useTestStore from '../store/testStore';

// Prosta ikona strzałki (chevron) jako komponent
const ChevronIcon = ({ expanded }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}>
        <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
);

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

    // Lokalny stan do śledzenia, która kategoria jest rozwinięta
    const [expandedCategory, setExpandedCategory] = useState(null);

    useEffect(() => { fetchAvailableTests(); }, [fetchAvailableTests]);

    // Grupujemy testy po kategorii za pomocą useMemo dla optymalizacji
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
        // Rozwiń klikniętą kategorię lub zwiń, jeśli już jest rozwinięta
        setExpandedCategory(prev => (prev === category ? null : category));
    };

    const handleSelectAll = (tests, areAllSelected) => {
        tests.forEach(test => {
            const isCurrentlySelected = selectedCategories.includes(test.test_id);
            // Jeśli odznaczamy wszystko, a test jest zaznaczony -> odznacz go
            if (areAllSelected && isCurrentlySelected) {
                toggleCategory(test.test_id);
            }
            // Jeśli zaznaczamy wszystko, a test nie jest zaznaczony -> zaznacz go
            else if (!areAllSelected && !isCurrentlySelected) {
                toggleCategory(test.test_id);
            }
        });
    };
    
    const isStartButtonDisabled = isLoading || selectedCategories.length === 0;

    return (
        <div className="main-card w-full max-w-2xl mx-auto p-8 md:p-12 text-center fade-in">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">Wybierz Kategorię</h1>
            <p className="text-lg text-gray-300 mb-8">Sprawdź swoją wiedzę w różnych dziedzinach.</p>
            
            {error && <p className="text-red-400 bg-red-900/50 p-3 rounded-md mb-6">{error}</p>}
            
            <div className="mb-8 text-left">
                {isLoading && availableTests.length === 0 && <p className="text-center">Ładowanie listy testów...</p>}
                
                <div className="space-y-4">
                    {Object.entries(testsByCategory).map(([category, tests]) => {
                        const allTestIds = tests.map(t => t.test_id);
                        const selectedCount = allTestIds.filter(id => selectedCategories.includes(id)).length;
                        const areAllSelected = selectedCount === allTestIds.length;

                        return (
                            // KLUCZOWA ZMIANA: Dodałem z powrotem klasę hover:border-brand-primary
                            <div key={category} className="bg-option-bg border border-card-border rounded-lg transition-all duration-300 hover:border-brand-primary">
                                <button 
                                    onClick={() => handleCategoryClick(category)} 
                                    className="w-full flex justify-between items-center p-5 font-bold text-xl text-white rounded-t-lg"
                                >
                                    <span>{category}</span>
                                    <ChevronIcon expanded={expandedCategory === category} />
                                </button>
                                
                                <div className={`grid transition-[grid-template-rows] duration-300 ease-in-out ${expandedCategory === category ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
                                    <div className="overflow-hidden">
                                        <div className="p-5 border-t border-card-border space-y-4">
                                            <label className="flex items-center w-full cursor-pointer p-3 rounded-md bg-black/20 hover:bg-black/40 transition-colors">
                                                <input
                                                    type="checkbox"
                                                    checked={areAllSelected}
                                                    onChange={() => handleSelectAll(tests, areAllSelected)}
                                                    className="h-5 w-5 rounded bg-gray-700 border-gray-600 text-brand-primary focus:ring-brand-primary"
                                                />
                                                <span className="ml-3 font-semibold text-gray-200">Zaznacz całą kategorię</span>
                                            </label>

                                            <div className="space-y-3 pl-3 border-l-2 border-gray-700/50">
                                                {tests.map(test => (
                                                    <label key={test.test_id} className="flex items-center cursor-pointer p-2 rounded-md hover:bg-white/5 transition-colors">
                                                        <input
                                                            type="checkbox"
                                                            checked={selectedCategories.includes(test.test_id)}
                                                            onChange={() => toggleCategory(test.test_id)}
                                                            className="h-5 w-5 rounded bg-gray-700 border-gray-600 text-brand-primary focus:ring-brand-primary"
                                                        />
                                                        <span className="ml-3 text-gray-200">{test.scope} ({test.version})</span>
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

            <div className="mb-8 text-left p-6 bg-black/20 rounded-lg border border-solid border-gray-700">
                <h2 className="text-xl font-semibold text-white mb-4">Ustawienia</h2>
                <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-6 space-y-4 sm:space-y-0">
                    <div className="flex-1">
                        <label htmlFor="num-questions" className="block text-sm font-medium text-gray-300 mb-1">Liczba pytań</label>
                        <input 
                            type="number" 
                            id="num-questions" 
                            className="w-full p-2 bg-gray-900 border border-gray-600 rounded-md text-white focus:ring-brand-primary focus:border-brand-primary" 
                            value={numQuestionsConfig} 
                            onChange={(e) => setConfig(parseInt(e.target.value, 10) || 1, timerEnabled)} 
                        />
                    </div>
                    <div className="flex items-center pt-6">
                        <input 
                            id="timer-enabled" 
                            type="checkbox" 
                            className="h-5 w-5 rounded bg-gray-700 border-gray-600 text-brand-primary focus:ring-brand-primary"
                            checked={timerEnabled} 
                            onChange={(e) => setConfig(numQuestionsConfig, e.target.checked)} 
                        />
                        <label htmlFor="timer-enabled" className="ml-3 block font-medium text-gray-300">Włącz licznik</label>
                    </div>
                </div>
            </div>

            <button onClick={startTest} disabled={isStartButtonDisabled} className="bg-brand-primary text-white font-bold py-3 px-10 rounded-full text-lg shadow-primary hover:bg-brand-primary-hover hover:shadow-primary-hover disabled:bg-gray-700 disabled:shadow-none disabled:cursor-not-allowed transition-all duration-300 ease-in-out hover:-translate-y-0.5 disabled:transform-none">
                {isLoading ? "Ładowanie..." : "Rozpocznij Test"}
            </button>
        </div>
    );
};
export default TestSetupPage;