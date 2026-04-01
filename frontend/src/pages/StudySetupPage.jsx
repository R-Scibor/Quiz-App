import React, { useState, useMemo } from 'react';
import useTestStore from '/src/store/testStore.js';
import { motion } from 'framer-motion';
import AnimatedCheckbox from '/src/components/AnimatedCheckbox.jsx';

const PRESET_COUNTS = [5, 10, 20];

const StatPill = ({ label, count, colorClass }) => (
    <div className={`flex flex-col items-center px-4 py-2 rounded-lg border ${colorClass}`}>
        <span className="text-xl font-bold">{count}</span>
        <span className="text-xs mt-0.5">{label}</span>
    </div>
);

const ChevronIcon = ({ expanded }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}>
        <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
);

const StudySetupPage = () => {
    const { studySetupData, studyNumQuestions, startStudyMode, setStudyConfig, resetTest, isLoading, user } = useTestStore();

    const EXCLUDED_KEY = `study_excluded_tests_${user?.username || 'guest'}`;
    const totalQueued = studySetupData?.total_queued ?? 0;
    const studiedTests = studySetupData?.studied_tests ?? [];
    const allTestIds = useMemo(() => studiedTests.map(t => String(t.id)), [studiedTests]);

    // Initialize session length: use persisted preference, capped at available
    const [numInput, setNumInput] = useState(() => {
        const max = totalQueued || studyNumQuestions;
        return String(Math.min(studyNumQuestions, Math.max(max, 1)));
    });
    const [inputError, setInputError] = useState('');

    // Initialize topic selection from localStorage-persisted exclusions
    const [selectedTestIds, setSelectedTestIds] = useState(() => {
        const excluded = new Set(JSON.parse(localStorage.getItem(EXCLUDED_KEY) || '[]'));
        return new Set(allTestIds.filter(id => !excluded.has(id)));
    });

    const [topicsExpanded, setTopicsExpanded] = useState(false);

    const areAllSelected = allTestIds.length > 0 && allTestIds.every(id => selectedTestIds.has(id));
    const noneSelected = selectedTestIds.size === 0;

    const toggleTest = (testId) => {
        const next = new Set(selectedTestIds);
        if (next.has(testId)) next.delete(testId);
        else next.add(testId);
        setSelectedTestIds(next);
        const excluded = allTestIds.filter(id => !next.has(id));
        localStorage.setItem(EXCLUDED_KEY, JSON.stringify(excluded));
    };

    const handleSelectAll = () => {
        setSelectedTestIds(new Set(allTestIds));
        localStorage.setItem(EXCLUDED_KEY, JSON.stringify([]));
    };

    const handleDeselectAll = () => {
        setSelectedTestIds(new Set());
        localStorage.setItem(EXCLUDED_KEY, JSON.stringify(allTestIds));
    };

    const handleNumChange = (e) => {
        const val = e.target.value;
        setNumInput(val);
        if (val === '') { setInputError('Enter a number.'); return; }
        const n = parseInt(val, 10);
        if (isNaN(n) || n <= 0) setInputError('Must be greater than 0.');
        else if (totalQueued > 0 && n > totalQueued) setInputError(`Max available: ${totalQueued}.`);
        else setInputError('');
    };

    const handlePreset = (n) => {
        const capped = totalQueued > 0 ? Math.min(n, totalQueued) : n;
        setNumInput(String(capped));
        setInputError('');
    };

    const handleStart = () => {
        const num = parseInt(numInput, 10);
        if (isNaN(num) || num <= 0 || noneSelected) return;
        const testIds = areAllSelected ? null : Array.from(selectedTestIds);
        setStudyConfig(num, testIds);
        startStudyMode();
    };

    const isStartDisabled = isLoading || noneSelected || !!inputError || numInput === '' || parseInt(numInput, 10) <= 0;

    if (!studySetupData) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto p-8 md:p-12 text-center"
            >
                <p className="text-gray-600 dark:text-gray-400">Loading study data...</p>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto p-8 md:p-12 text-center"
        >
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">Study Mode</h1>
            <p className="text-gray-600 dark:text-gray-300 mb-8">Review questions based on your spaced repetition schedule.</p>

            {/* Queue breakdown */}
            <div className="flex flex-wrap justify-center gap-3 mb-8">
                <StatPill
                    label="Due"
                    count={studySetupData.due_count}
                    colorClass="border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20"
                />
                <StatPill
                    label="Struggling"
                    count={studySetupData.struggling_count}
                    colorClass="border-yellow-300 dark:border-yellow-700 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20"
                />
                <StatPill
                    label="New"
                    count={studySetupData.new_count}
                    colorClass="border-blue-300 dark:border-blue-700 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20"
                />
                <StatPill
                    label="Mastered"
                    count={studySetupData.mastered_count}
                    colorClass="border-green-300 dark:border-green-700 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20"
                />
            </div>

            {/* Session length */}
            <div className="mb-8 text-left">
                <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-3">Session length</h2>
                <div className="flex flex-wrap gap-2 mb-3">
                    {PRESET_COUNTS.map(n => {
                        const capped = totalQueued > 0 ? Math.min(n, totalQueued) : n;
                        const isActive = parseInt(numInput, 10) === capped && !inputError;
                        return (
                            <button
                                key={n}
                                onClick={() => handlePreset(n)}
                                className={`px-5 py-2 rounded-full border text-sm font-medium transition-all ${
                                    isActive
                                        ? 'border-brand-primary bg-brand-primary/10 text-brand-primary'
                                        : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-brand-primary hover:text-brand-primary'
                                }`}
                            >
                                {n}
                            </button>
                        );
                    })}
                    <input
                        type="number"
                        value={numInput}
                        onChange={handleNumChange}
                        min={1}
                        max={totalQueued || undefined}
                        className="w-20 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-transparent text-gray-800 dark:text-white text-sm text-center focus:outline-none focus:border-brand-primary"
                        placeholder="Custom"
                    />
                </div>
                {inputError && <p className="text-red-500 text-xs mt-1">{inputError}</p>}
                {totalQueued > 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">{totalQueued} questions available in queue</p>
                )}
            </div>

            {/* Topic filter — only shown when more than one topic */}
            {studiedTests.length > 1 && (
                <div className="mb-8 text-left">
                    <motion.button
                        onClick={() => setTopicsExpanded(v => !v)}
                        className="w-full flex justify-between items-center py-3 px-4 rounded-lg bg-gray-100 dark:bg-option-bg border border-gray-300 dark:border-card-border text-gray-800 dark:text-white font-semibold"
                        whileTap={{ scale: 0.99 }}
                    >
                        <span>Topics <span className="font-normal text-sm text-gray-500 dark:text-gray-400">({selectedTestIds.size}/{studiedTests.length} selected)</span></span>
                        <ChevronIcon expanded={topicsExpanded} />
                    </motion.button>

                    <div className={`grid transition-[grid-template-rows] duration-300 ease-in-out ${topicsExpanded ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
                        <div className="overflow-hidden">
                            <div className="pt-3 space-y-3">
                                {/* Select / deselect all */}
                                <div className="flex gap-2">
                                    <button
                                        onClick={handleSelectAll}
                                        disabled={areAllSelected}
                                        className="text-xs px-3 py-1 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-brand-primary hover:text-brand-primary disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                    >
                                        Select all
                                    </button>
                                    <button
                                        onClick={handleDeselectAll}
                                        disabled={noneSelected}
                                        className="text-xs px-3 py-1 rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-red-400 hover:text-red-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                    >
                                        Deselect all
                                    </button>
                                </div>

                                {/* Test list */}
                                <div className="space-y-2">
                                    {studiedTests.map(test => {
                                        const id = String(test.id);
                                        return (
                                            <div key={id} className="p-3 rounded-md bg-gray-100 dark:bg-option-bg hover:bg-gray-200 dark:hover:bg-white/5 transition-colors">
                                                <AnimatedCheckbox
                                                    id={`study-topic-${id}`}
                                                    checked={selectedTestIds.has(id)}
                                                    onChange={() => toggleTest(id)}
                                                >
                                                    <AnimatedCheckbox.Indicator />
                                                    <AnimatedCheckbox.Label>{test.title}</AnimatedCheckbox.Label>
                                                </AnimatedCheckbox>
                                            </div>
                                        );
                                    })}
                                </div>

                                {noneSelected && (
                                    <p className="text-xs text-red-500">Select at least one topic to start.</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Start button */}
            <motion.button
                onClick={handleStart}
                disabled={isStartDisabled}
                whileHover={isStartDisabled ? {} : { scale: 1.03 }}
                whileTap={isStartDisabled ? {} : { scale: 0.97 }}
                className="btn-primary w-full py-3 px-8 rounded-full text-lg font-bold shadow-primary hover:shadow-primary-hover transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {isLoading ? 'Loading...' : 'Start Study Session'}
            </motion.button>
        </motion.div>
    );
};

export default StudySetupPage;
