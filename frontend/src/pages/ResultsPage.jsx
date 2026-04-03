import React, { useMemo, useState, useEffect } from 'react';
import useTestStore from '../store/testStore';

const ResultsPage = () => {
    const {
        score, currentQuestions, resetTest, retryTest, timerEnabled, totalTimeSpent, reviewAnswers,
        userAnswers, openQuestionResults, availableTests,
    } = useTestStore();

    const totalMaxPoints = useMemo(() => {
        return currentQuestions.reduce((total, question) => {
            // Dla pytań zamkniętych przyjmujemy 1 pkt, dla otwartych bierzemy maxPoints
            return total + (question.maxPoints || 1);
        }, 0);
    }, [currentQuestions]);

    const incorrectAnswers = totalMaxPoints - score;
    const percentage = totalMaxPoints > 0 ? Math.round((score / totalMaxPoints) * 100) : 0;

    const timeTaken = useMemo(() => {
        if (!timerEnabled) {
            return null;
        }
        return totalTimeSpent;
    }, [timerEnabled, totalTimeSpent]);

    const formatTime = (totalSeconds) => {
        if (typeof totalSeconds !== 'number' || isNaN(totalSeconds)) {
            return '00:00';
        }
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    };

    // Per-category breakdown — only computed when quiz spans 2+ distinct tests
    const categoryBreakdown = useMemo(() => {
        const byTest = {};
        currentQuestions.forEach(q => {
            if (!byTest[q.test_id]) {
                const meta = availableTests.find(t => t.test_id === q.test_id);
                byTest[q.test_id] = { title: meta?.scope || 'Unknown', earned: 0, possible: 0 };
            }
            const entry = byTest[q.test_id];
            const maxPts = q.maxPoints || 1;
            entry.possible += maxPts;
            const isOpen = q.type === 'open-text' || q.type === 'open-cli' || q.type === 'open-code';
            if (isOpen) {
                entry.earned += openQuestionResults[q.id]?.points_awarded ?? 0;
            } else {
                const ua = userAnswers[q.id];
                const ca = q.correctAnswers;
                let correct = false;
                if (Array.isArray(ca) && Array.isArray(ua)) {
                    correct = [...ua].sort().join(',') === [...ca].sort().join(',');
                } else {
                    correct = ua === ca;
                }
                if (correct) entry.earned += maxPts;
            }
        });
        return Object.values(byTest).sort((a, b) => b.possible - a.possible);
    }, [currentQuestions, userAnswers, openQuestionResults, availableTests]);

    const showBreakdown = categoryBreakdown.length >= 2;

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
                    <p className="text-2xl font-bold text-gray-800 dark:text-white">{score} / {totalMaxPoints}</p>
                </div>
                <div>
                    <p className="text-lg text-gray-500 dark:text-gray-400">Uzyskane</p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">{score}</p>
                </div>
                <div>
                    <p className="text-lg text-gray-500 dark:text-gray-400">Stracone</p>
                    <p className="text-2xl font-bold text-red-600 dark:text-brand-primary">{incorrectAnswers}</p>
                </div>
            </div>

            {showBreakdown && (
                <div className="mb-10 text-left">
                    <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                        Per-topic breakdown
                    </h3>
                    <div className="space-y-3">
                        {categoryBreakdown.map(({ title, earned, possible }) => {
                            const pct = possible > 0 ? Math.round((earned / possible) * 100) : 0;
                            const colorClass = pct >= 80
                                ? 'bg-green-500'
                                : pct >= 50
                                ? 'bg-yellow-500'
                                : 'bg-red-500';
                            const textColorClass = pct >= 80
                                ? 'text-green-600 dark:text-green-400'
                                : pct >= 50
                                ? 'text-yellow-600 dark:text-yellow-400'
                                : 'text-red-600 dark:text-red-400';
                            return (
                                <div key={title}>
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate mr-3">{title}</span>
                                        <span className="text-sm text-gray-500 dark:text-gray-400 shrink-0">
                                            {earned % 1 === 0 ? earned : earned.toFixed(1)} / {possible}
                                            <span className={`ml-2 font-semibold ${textColorClass}`}>{pct}%</span>
                                        </span>
                                    </div>
                                    <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-2 rounded-full transition-all duration-700 ${colorClass}`}
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <button onClick={retryTest} className="btn-primary font-bold py-3 px-10 rounded-full text-lg w-full sm:w-auto flex items-center justify-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                    <span>Spróbuj Ponownie</span>
                </button>
                <button onClick={reviewAnswers} className="btn-primary font-bold py-3 px-10 rounded-full text-lg w-full sm:w-auto">
                    <span>Przeglądaj odpowiedzi</span>
                </button>
            </div>
        </div>
    );
};

export default ResultsPage;
