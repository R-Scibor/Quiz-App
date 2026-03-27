import React, { useEffect, useState } from 'react';
import useTestStore from '../store/testStore';
import { motion } from 'framer-motion';

const CircleProgress = ({ percentage }) => {
    const radius = 70;
    const circumference = 2 * Math.PI * radius;
    const [offset, setOffset] = useState(circumference);

    useEffect(() => {
        const timer = setTimeout(() => {
            setOffset(circumference - (percentage / 100) * circumference);
        }, 100);
        return () => clearTimeout(timer);
    }, [percentage, circumference]);

    return (
        <div className="relative flex items-center justify-center">
            <svg className="progress-ring w-40 h-40">
                <circle className="text-gray-200 dark:text-gray-700" strokeWidth="10" stroke="currentColor" fill="transparent" r={radius} cx="80" cy="80" />
                <circle className="progress-ring__circle text-brand-primary" strokeWidth="10" stroke="currentColor" fill="transparent" r={radius} cx="80" cy="80"
                    style={{ strokeDasharray: circumference, strokeDashoffset: offset }} />
            </svg>
            <div className="absolute">
                <p className="text-4xl font-bold text-gray-800 dark:text-white">{percentage}%</p>
            </div>
        </div>
    );
};

const StatCard = ({ label, value, sub }) => (
    <div className="bg-gray-50 dark:bg-black/20 rounded-xl p-5 text-center">
        <p className="text-2xl font-bold text-gray-800 dark:text-white">{value}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{label}</p>
        {sub && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{sub}</p>}
    </div>
);

const StatsPage = () => {
    const { fetchStats, userStats, statsLoading, resetTest } = useTestStore();

    useEffect(() => {
        fetchStats();
    }, []);

    if (statsLoading) {
        return (
            <div className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto rounded-2xl shadow-2xl p-12 flex items-center justify-center">
                <p className="text-gray-500 dark:text-gray-400">Loading stats…</p>
            </div>
        );
    }

    if (!userStats) {
        return (
            <div className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto rounded-2xl shadow-2xl p-12 text-center">
                <p className="text-gray-500 dark:text-gray-400 mb-6">No stats available yet. Complete a quiz to get started.</p>
                <button onClick={resetTest} className="btn-primary font-bold py-2 px-8 rounded-full">Back to Home</button>
            </div>
        );
    }

    const {
        total_sessions, total_questions_answered, overall_accuracy,
        current_streak_days, longest_streak_days, avg_time_per_question,
        recent_sessions,
    } = userStats;

    return (
        <motion.div
            className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto rounded-2xl shadow-2xl overflow-hidden"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
        >
            <div className="p-8 md:p-10">
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold text-gray-800 dark:text-white">My Stats</h2>
                    <button onClick={resetTest} className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                        ← Home
                    </button>
                </div>

                <div className="flex flex-col md:flex-row items-center gap-8 mb-8">
                    <CircleProgress percentage={overall_accuracy} />
                    <div className="grid grid-cols-2 gap-4 flex-1 w-full">
                        <StatCard label="Sessions" value={total_sessions} />
                        <StatCard label="Questions answered" value={total_questions_answered} />
                        <StatCard label="Current streak" value={`${current_streak_days}d`} sub={`Best: ${longest_streak_days}d`} />
                        <StatCard label="Avg time / question" value={avg_time_per_question > 0 ? `${avg_time_per_question}s` : '—'} />
                    </div>
                </div>

                {recent_sessions.length > 0 && (
                    <div>
                        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-3">Recent sessions</h3>
                        <div className="space-y-2">
                            {recent_sessions.map(s => (
                                <div key={s.id} className="flex items-center justify-between bg-gray-50 dark:bg-black/20 rounded-lg px-4 py-3">
                                    <span className="text-sm text-gray-500 dark:text-gray-400">{s.date}</span>
                                    <span className="text-sm text-gray-700 dark:text-gray-300">
                                        {s.correct_count} / {s.total_questions} correct
                                    </span>
                                    <span className={`text-sm font-semibold ${s.accuracy >= 70 ? 'text-green-500' : s.accuracy >= 40 ? 'text-yellow-500' : 'text-red-500'}`}>
                                        {s.accuracy}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default StatsPage;
