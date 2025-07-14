import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { reportIssue } from '../services/api';
import LoadingSpinner from './LoadingSpinner';

const ReportModal = ({ question, testId, aiFeedback, onClose, onReportSuccess }) => {
    const [issueType, setIssueType] = useState('');
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
        <AnimatePresence>
            <motion.div
                className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4"
                variants={backdropVariants}
                initial="hidden"
                animate="visible"
                exit="hidden"
                onClick={onClose}
            >
                <motion.div
                    className="bg-white dark:bg-card-bg rounded-xl shadow-2xl p-8 w-full max-w-lg relative"
                    variants={modalVariants}
                    onClick={(e) => e.stopPropagation()}
                >
                    {success ? (
                        <div className="text-center">
                            <h3 className="text-2xl font-bold text-green-500 mb-4">Dziękujemy!</h3>
                            <p className="text-gray-700 dark:text-gray-300">Twoje zgłoszenie zostało pomyślnie wysłane.</p>
                        </div>
                    ) : (
                        <>
                            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-6">Zgłoś problem</h2>
                            <form onSubmit={handleSubmit}>
                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Typ problemu:</label>
                                    <div className="flex flex-col sm:flex-row gap-4">
                                        <button type="button" onClick={() => setIssueType('QUESTION_ERROR')} className={`report-option-btn ${issueType === 'QUESTION_ERROR' ? 'selected' : ''}`}>
                                            Błąd w pytaniu / odpowiedzi
                                        </button>
                                        <button type="button" onClick={() => setIssueType('AI_GRADING_ERROR')} className={`report-option-btn ${issueType === 'AI_GRADING_ERROR' ? 'selected' : ''}`} disabled={!aiFeedback}>
                                            Niesłuszna ocena AI
                                            {!aiFeedback && <span className="text-xs block">(Niedostępne dla tego pytania)</span>}
                                        </button>
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

                                <div className="flex justify-end items-center gap-4">
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
            </motion.div>
        </AnimatePresence>
    );
};

export default ReportModal;