import React, { useMemo } from 'react';
import useTestStore from '../store/testStore';

const ResultsPage = () => {
    const { score, currentQuestions, testStartTime, testEndTime, resetTest } = useTestStore();
    const totalQuestions = currentQuestions.length;
    const percentage = totalQuestions > 0 ? Math.round((score / totalQuestions) * 100) : 0;
    
    const timeTaken = useMemo(() => {
        if (!testStartTime || !testEndTime) return null;
        const seconds = Math.floor((new Date(testEndTime) - new Date(testStartTime)) / 1000);
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }, [testStartTime, testEndTime]);

    return (
        <div className="w-full max-w-2xl mx-auto p-8 bg-white rounded-xl shadow-lg text-center">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">Test ukończony!</h1>
            <h2 className="text-2xl font-semibold text-gray-600 mb-6">Twój wynik:</h2>
            <div className="my-8">
                <p className="text-6xl font-bold text-blue-600">{`${score} / ${totalQuestions}`}</p>
                <p className="text-3xl text-gray-700 mt-2">{`(${percentage}%)`}</p>
            </div>
            {timeTaken && <p className="text-lg text-gray-500 mb-8">Czas ukończenia: <span className="font-bold">{timeTaken}</span></p>}
            <button onClick={resetTest} className="bg-blue-600 text-white font-bold py-3 px-8 rounded-lg hover:bg-blue-700">
                Spróbuj ponownie
            </button>
        </div>
    );
};
export default ResultsPage;
