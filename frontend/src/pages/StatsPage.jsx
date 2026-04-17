import React, { useEffect } from 'react';
import useTestStore from '../store/testStore';
import { motion } from 'framer-motion';

const CircleProgress = ({ percentage }) => {
    const radius = 70;
    const circumference = 2 * Math.PI * radius;
    const [offset, setOffset] = React.useState(circumference);

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

const accuracyColor = (pct) => {
    if (pct >= 80) return 'text-green-600 dark:text-green-400';
    if (pct >= 50) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
};

const accuracyBarColor = (pct) => {
    if (pct >= 80) return 'bg-green-500';
    if (pct >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
};

// Simple dot sparkline — each dot represents one session, oldest left → newest right
const AccuracySparkline = ({ sessions }) => {
    if (!sessions || sessions.length < 2) return null;
    const ordered = [...sessions].reverse(); // API returns newest-first, we want oldest-first
    return (
        <div>
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                Accuracy trend
            </h3>
            <div className="flex items-end gap-1.5 h-10">
                {ordered.map((s, i) => {
                    const height = Math.max(20, s.accuracy); // min height so 0% still shows
                    return (
                        <div
                            key={s.id || i}
                            title={`${s.date}: ${s.accuracy}%`}
                            className={`flex-1 rounded-sm transition-all duration-500 ${accuracyBarColor(s.accuracy)}`}
                            style={{ height: `${height}%` }}
                        />
                    );
                })}
            </div>
            <div className="flex justify-between mt-1">
                <span className="text-xs text-gray-400 dark:text-gray-500">{ordered[0]?.date}</span>
                <span className="text-xs text-gray-400 dark:text-gray-500">{ordered[ordered.length - 1]?.date}</span>
            </div>
        </div>
    );
};

const StatsPage = () => {
    const { fetchStats, userStats, testStats, statsLoading, goToHome } = useTestStore();

    useEffect(() => {
        fetchStats();
        // eslint-disable-next-line react-hooks/exhaustive-deps
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
                <button onClick={goToHome} className="btn-primary font-bold py-2 px-8 rounded-full">Back to Home</button>
            </div>
        );
    }

    const {
        total_sessions, total_questions_answered, overall_accuracy,
        current_streak_days, longest_streak_days, avg_time_per_question,
        recent_sessions,
        questions_by_type, study_sessions, regular_sessions,
    } = userStats;

    return (
        <motion.div
            className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto rounded-2xl shadow-2xl overflow-hidden"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
        >
            <div className="p-8 md:p-10 space-y-8">
                {/* Header */}
                <h2 className="text-3xl font-bold text-gray-800 dark:text-white">My Stats</h2>

                {/* Overall accuracy + core stats */}
                <div className="flex flex-col md:flex-row items-center gap-8">
                    <CircleProgress percentage={overall_accuracy} />
                    <div className="grid grid-cols-2 gap-4 flex-1 w-full">
                        <StatCard label="Sessions" value={total_sessions} />
                        <StatCard label="Questions answered" value={total_questions_answered} />
                        <StatCard label="Current streak" value={`${current_streak_days}d`} sub={`Best: ${longest_streak_days}d`} />
                        <StatCard label="Avg time / question" value={avg_time_per_question > 0 ? `${avg_time_per_question}s` : '—'} />
                    </div>
                </div>

                {/* Session type + question type breakdown */}
                {(questions_by_type || study_sessions !== undefined) && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                            Breakdown
                        </h3>
                        <div className="grid grid-cols-3 gap-3">
                            <StatCard label="Regular sessions" value={regular_sessions ?? '—'} />
                            <StatCard label="Study sessions" value={study_sessions ?? '—'} />
                            <StatCard label="Closed / Open" value={questions_by_type ? `${questions_by_type.closed} / ${questions_by_type.open}` : '—'} sub="questions answered" />
                        </div>
                    </div>
                )}

                {/* Per-test breakdown */}
                {testStats && testStats.length > 0 && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                            Per-test performance
                        </h3>
                        <div className="space-y-3">
                            {testStats.slice(0, 10).map(t => (
                                <div key={t.test_id}>
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate mr-3" title={t.title}>
                                            {t.title}
                                        </span>
                                        <span className="text-xs text-gray-400 dark:text-gray-500 shrink-0">
                                            {t.points_earned}/{t.points_possible} pts
                                            {t.avg_time_secs > 0 && <span className="ml-2">{t.avg_time_secs}s avg</span>}
                                            <span className={`ml-2 font-semibold ${accuracyColor(t.accuracy)}`}>{t.accuracy}%</span>
                                        </span>
                                    </div>
                                    <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-1.5 rounded-full transition-all duration-700 ${accuracyBarColor(t.accuracy)}`}
                                            style={{ width: `${t.accuracy}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Accuracy trend sparkline */}
                {recent_sessions && recent_sessions.length >= 2 && (
                    <AccuracySparkline sessions={recent_sessions} />
                )}

                {/* Recent sessions list */}
                {recent_sessions && recent_sessions.length > 0 && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                            Recent sessions
                        </h3>
                        <div className="space-y-2">
                            {recent_sessions.map(s => (
                                <div key={s.id} className="flex items-center justify-between bg-gray-50 dark:bg-black/20 rounded-lg px-4 py-3">
                                    <span className="text-sm text-gray-500 dark:text-gray-400">{s.date}</span>
                                    <span className="text-sm text-gray-700 dark:text-gray-300">
                                        {s.score_achieved} / {s.score_possible} pts
                                    </span>
                                    <span className={`text-sm font-semibold ${accuracyColor(s.accuracy)}`}>
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
