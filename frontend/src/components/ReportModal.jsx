import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { reportIssue } from '../services/api';
import LoadingSpinner from './LoadingSpinner';

const ReportModal = ({ question, testId, aiFeedback, onClose, onReportSuccess }) => {
    const [issueType, setIssueType] = useState('QUESTION_ERROR');
    const [description, setDescription] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!issueType) {
            setError('Proszę wybrać typ problemu.');
            return;
        }
        
        setIsSubmitting(true);
        setError(null);

        const payload = {
            question: question.id,
            test: testId,
            issue_type: issueType,
            description: description,
            ai_feedback_snapshot: issueType === 'AI_GRADING_ERROR' ? JSON.stringify(aiFeedback) : null,
        };

        try {
            await reportIssue(payload);
            setSuccess(true);
            setTimeout(() => {
                onReportSuccess();
                onClose();
            }, 2000);
        } catch (err) {
            setError(err.message || 'Wystąpił błąd podczas wysyłania zgłoszenia.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const backdropVariants = {
        hidden: { opacity: 0 },
        visible: { opacity: 1 },
    };

    const modalVariants = {
        hidden: { opacity: 0, y: "-50px" },
        visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 30 } },
        exit: { opacity: 0, y: "50px" },
    };

    return (
        <motion.div
            className="bg-white dark:bg-card-bg rounded-xl shadow-2xl p-8 w-full h-full relative"
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
        >
            {success ? (
                <div className="text-center">
                    <h3 className="text-2xl font-bold text-green-500 mb-4">Dziękujemy!</h3>
                    <p className="text-gray-700 dark:text-gray-300">Twoje zgłoszenie zostało pomyślnie wysłane.</p>
                </div>
            ) : (
                <>
                    <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">Zgłoś problem</h2>
                    <form onSubmit={handleSubmit} className="flex flex-col h-full">
                        <div className="flex-grow">
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Typ problemu:</label>
                                <div className="space-y-3">
                                    <div className="flex items-center">
                                        <input
                                            type="radio"
                                            id="question_error"
                                            name="issueType"
                                            value="QUESTION_ERROR"
                                            checked={issueType === 'QUESTION_ERROR'}
                                            onChange={(e) => setIssueType(e.target.value)}
                                            className="h-4 w-4 border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-option-bg"
                                        />
                                        <label htmlFor="question_error" className="ml-3 block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Błąd w pytaniu / odpowiedzi
                                        </label>
                                    </div>
                                    {question.type === 'open-ended' && (
                                        <div className="flex items-center">
                                            <input
                                                type="radio"
                                                id="ai_grading_error"
                                                name="issueType"
                                                value="AI_GRADING_ERROR"
                                                checked={issueType === 'AI_GRADING_ERROR'}
                                                onChange={(e) => setIssueType(e.target.value)}
                                                disabled={!aiFeedback}
                                                className="h-4 w-4 border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-option-bg"
                                            />
                                            <label htmlFor="ai_grading_error" className={`ml-3 block text-sm font-medium ${!aiFeedback ? 'text-gray-400 dark:text-gray-500' : 'text-gray-700 dark:text-gray-300'}`}>
                                                Niesłuszna ocena AI
                                                {!aiFeedback && <span className="text-xs block">(Niedostępne dla tego pytania)</span>}
                                            </label>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="mb-6">
                                <label htmlFor="description" className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                                    Opcjonalne uzasadnienie:
                                </label>
                                <textarea
                                    id="description"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="Opisz problem bardziej szczegółowo..."
                                    className="w-full h-28 p-3 rounded-lg bg-gray-100 dark:bg-option-bg border-2 border-gray-300 dark:border-gray-600 focus:border-brand-primary focus:ring-brand-primary transition-colors text-gray-900 dark:text-white"
                                />
                            </div>

                            {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}
                        </div>

                        <div className="flex justify-end items-center gap-4 mt-auto">
                            <button type="button" onClick={onClose} className="btn-secondary py-2 px-6">
                                Anuluj
                            </button>
                            <button type="submit" className="btn-primary py-2 px-6" disabled={isSubmitting || !issueType}>
                                {isSubmitting ? <LoadingSpinner size="sm" /> : 'Wyślij zgłoszenie'}
                            </button>
                        </div>
                    </form>
                </>
            )}
        </motion.div>
    );
};

export default ReportModal;