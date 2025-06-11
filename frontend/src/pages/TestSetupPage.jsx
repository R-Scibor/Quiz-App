// --- PLIK: src/pages/TestSetupPage.jsx ---
import React, { useEffect } from 'react';
import useTestStore from '../store/testStore';

// Ikony dla lepszej wizualizacji ustawień
const ListChecksIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m3 17 2 2 4-4" /><path d="m3 7 2 2 4-4" /><path d="M13 6h8" /><path d="M13 12h8" /><path d="M13 18h8" />
  </svg>
);

const TimerIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
  </svg>
);

const CheckCircleIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-teal-400">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>
);


const TestSetupPage = () => {
    const { availableTests, fetchAvailableTests, isLoading, error, selectedCategories, toggleCategory, numQuestionsConfig, timerEnabled, setConfig, startTest } = useTestStore();

    useEffect(() => { fetchAvailableTests(); }, [fetchAvailableTests]);

    return (
        // Tło z gradientem dla całej strony
        <div className="w-full min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-slate-900 p-4">
            
            {/* Główny kontener z efektem "glassmorphism" */}
            <div className="w-full max-w-2xl mx-auto bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 text-white p-8 transition-all duration-500">
                
                <h1 className="text-4xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-teal-200 to-cyan-400 mb-2">Skonfiguruj Test</h1>
                <p className="text-center text-gray-300 mb-8">Wybierz dziedziny i dostosuj ustawienia, aby zacząć.</p>
                
                {error && <p className="text-red-400 bg-red-900/50 p-3 rounded-md mb-4 text-center">{error}</p>}
                
                <div className="mb-8">
                    <h2 className="text-xl font-semibold text-gray-100 mb-4 border-b border-white/20 pb-2">Kategorie</h2>
                    {isLoading && availableTests.length === 0 && <p className="text-center text-gray-400">Ładowanie listy testów...</p>}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {availableTests.map((test) => {
                            const isSelected = selectedCategories.includes(test.test_id);
                            return (
                                <label 
                                    key={test.test_id} 
                                    className={`relative flex items-center p-4 rounded-lg cursor-pointer transition-all duration-300 ${isSelected ? 'bg-teal-500/30 border-teal-400' : 'bg-white/10 hover:bg-white/20 border-transparent'} border-2`}
                                    onClick={() => toggleCategory(test.test_id)}
                                >
                                    <input type="checkbox" className="hidden" checked={isSelected} readOnly />
                                    
                                    <div className="flex-grow">
                                        <p className="font-bold text-gray-50">{test.category}</p>
                                        <p className="text-sm text-gray-300">{test.scope} (v{test.version})</p>
                                    </div>
                                    
                                    {/* Wizualny wskaźnik zaznaczenia */}
                                    <div className={`w-7 h-7 flex items-center justify-center rounded-full transition-all duration-300 ${isSelected ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`}>
                                        <CheckCircleIcon />
                                    </div>
                                </label>
                            );
                        })}
                    </div>
                </div>

                <div className="mb-10">
                    <h2 className="text-xl font-semibold text-gray-100 mb-4 border-b border-white/20 pb-2">Ustawienia</h2>
                    <div className="flex flex-col sm:flex-row gap-6">
                        <div className="flex-1 flex items-center gap-4 bg-white/10 p-4 rounded-lg">
                            <TimerIcon />
                            <label htmlFor="timer-enabled" className="flex-grow text-gray-200 font-medium">Licznik czasu</label>
                            {/* Niestandardowy przełącznik */}
                            <button
                                id="timer-enabled"
                                onClick={() => setConfig(numQuestionsConfig, !timerEnabled)}
                                className={`relative inline-flex items-center h-6 rounded-full w-11 transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-cyan-500 ${timerEnabled ? 'bg-teal-500' : 'bg-gray-600'}`}
                            >
                                <span className={`inline-block w-4 h-4 transform bg-white rounded-full transition-transform duration-300 ${timerEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
                            </button>
                        </div>
                        <div className="flex-1 flex items-center gap-4 bg-white/10 p-4 rounded-lg">
                            <ListChecksIcon />
                            <label htmlFor="num-questions" className="text-gray-200 font-medium">Liczba pytań</label>
                            <input
                                type="number"
                                id="num-questions"
                                className="w-20 p-1 bg-transparent border-b-2 border-white/30 text-center text-white font-bold focus:outline-none focus:border-cyan-400 transition"
                                value={numQuestionsConfig}
                                onChange={(e) => setConfig(parseInt(e.target.value, 10) || 1, timerEnabled)}
                            />
                        </div>
                    </div>
                </div>

                <button
                    onClick={startTest}
                    disabled={isLoading || selectedCategories.length === 0}
                    className="w-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white font-bold text-lg py-3 px-4 rounded-lg hover:from-teal-600 hover:to-cyan-600 focus:outline-none focus:ring-4 focus:ring-cyan-500/50 disabled:from-gray-500 disabled:to-gray-600 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:scale-100"
                >
                    {isLoading ? "Ładowanie..." : "Rozpocznij Grę"}
                </button>
            </div>
        </div>
    );
};

export default TestSetupPage;
