import React, { useMemo, useState, useEffect } from 'react';
import useTestStore from '../store/testStore';

const ResultsPage = () => {
    const { score, currentQuestions, resetTest, timerEnabled, testStartTime, testEndTime } = useTestStore();
    
    const totalQuestions = currentQuestions.length;
    const incorrectAnswers = totalQuestions - score;
    const percentage = totalQuestions > 0 ? Math.round((score / totalQuestions) * 100) : 0;

    const timeTaken = useMemo(() => {
        if (!timerEnabled || !testStartTime || !testEndTime) {
            return null;
        }
        const start = new Date(testStartTime);
        const end = new Date(testEndTime);
        return Math.round((end - start) / 1000);
    }, [timerEnabled, testStartTime, testEndTime]);

    const formatTime = (totalSeconds) => {
        if (typeof totalSeconds !== 'number' || isNaN(totalSeconds)) {
            return '00:00';
        }
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    };

    const radius = 84;
    const circumference = 2 * Math.PI * radius;
    
    const [progressOffset, setProgressOffset] = useState(circumference);

    useEffect(() => {
        const offset = circumference - (percentage / 100) * circumference;
        const timer = setTimeout(() => setProgressOffset(offset), 100);
        return () => clearTimeout(timer);
    }, [percentage, circumference]);


    return (
        <div className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto rounded-xl p-8 md:p-12 text-center fade-in">
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-4">Quiz ukończony!</h1>
            <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">Oto Twoje wyniki.</p>
            
            <div className="relative flex items-center justify-center my-8">
                <svg className="progress-ring w-48 h-48">
                    <circle 
                        className="text-gray-200 dark:text-gray-700" 
                        strokeWidth="12" 
                        stroke="currentColor" 
                        fill="transparent" 
                        r={radius} 
                        cx="96" 
                        cy="96"
                    />
                    <circle 
                        className="progress-ring__circle text-brand-primary" 
                        strokeWidth="12" 
                        stroke="currentColor" 
                        fill="transparent" 
                        r={radius} 
                        cx="96" 
                        cy="96"
                        style={{
                            strokeDasharray: circumference,
                            strokeDashoffset: progressOffset,
                        }}
                    />
                </svg>
                <div className="absolute flex flex-col">
                     <p className="text-5xl font-bold text-gray-800 dark:text-white">{percentage}%</p>
                </div>
            </div>
            
            {timeTaken !== null && (
                <div className="mb-8">
                    <p className="text-lg text-gray-500 dark:text-gray-400">Czas ukończenia</p>
                    <p className="text-3xl font-bold text-gray-800 dark:text-white">{formatTime(timeTaken)}</p>
                </div>
            )}

            <div className="flex justify-around mb-10">
                <div>
                    <p className="text-lg text-gray-500 dark:text-gray-400">Wynik</p>
                    <p className="text-2xl font-bold text-gray-800 dark:text-white">{score} / {totalQuestions}</p>
                </div>
                <div>
                    <p className="text-lg text-gray-500 dark:text-gray-400">Poprawne</p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">{score}</p>
                </div>
                <div>
                    <p className="text-lg text-gray-500 dark:text-gray-400">Błędne</p>
                    <p className="text-2xl font-bold text-red-600 dark:text-brand-primary">{incorrectAnswers}</p>
                </div>
            </div>

            <button onClick={resetTest} className="btn-primary font-bold py-3 px-10 rounded-full text-lg">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                <span>Spróbuj Ponownie</span>
            </button>
        </div>
    );
};

export default ResultsPage;
