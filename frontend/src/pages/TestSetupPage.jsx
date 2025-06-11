import React, { useEffect } from 'react';
import useTestStore from '../store/testStore';

const TestSetupPage = () => {
    const { availableTests, fetchAvailableTests, isLoading, error, selectedCategories, toggleCategory, numQuestionsConfig, timerEnabled, setConfig, startTest } = useTestStore();

    useEffect(() => { fetchAvailableTests(); }, [fetchAvailableTests]);

    return (
        <div className="w-full max-w-2xl mx-auto p-8 bg-white rounded-xl shadow-lg">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Skonfiguruj swój test</h1>
            {error && <p className="text-red-500 bg-red-100 p-3 rounded-md mb-4">{error}</p>}
            
            <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-700 mb-3">1. Wybierz kategorie</h2>
                {isLoading && availableTests.length === 0 && <p>Ładowanie listy testów...</p>}
                <div className="space-y-2">
                    {availableTests.map((test) => (
                        <label key={test.test_id} className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer">
                            <input type="checkbox" className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500" checked={selectedCategories.includes(test.test_id)} onChange={() => toggleCategory(test.test_id)} />
                            <span className="ml-3 text-gray-800 font-medium">{`${test.category}: ${test.scope} (v${test.version})`}</span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-700 mb-3">2. Ustawienia</h2>
                <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-4 sm:space-y-0">
                    <div className="flex-1">
                        <label htmlFor="num-questions" className="block text-sm font-medium text-gray-700 mb-1">Liczba pytań</label>
                        <input type="number" id="num-questions" className="w-full p-2 border border-gray-300 rounded-md" value={numQuestionsConfig} onChange={(e) => setConfig(parseInt(e.target.value, 10) || 1, timerEnabled)} />
                    </div>
                    <div className="flex items-center pt-6">
                        <input id="timer-enabled" type="checkbox" className="h-5 w-5 rounded border-gray-300 text-blue-600" checked={timerEnabled} onChange={(e) => setConfig(numQuestionsConfig, e.target.checked)} />
                        <label htmlFor="timer-enabled" className="ml-2 block text-sm font-medium text-gray-900">Włącz licznik czasu</label>
                    </div>
                </div>
            </div>

            <button onClick={startTest} disabled={isLoading || selectedCategories.length === 0} className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-all">
                {isLoading ? "Ładowanie..." : "Rozpocznij Test"}
            </button>
        </div>
    );
};
export default TestSetupPage;