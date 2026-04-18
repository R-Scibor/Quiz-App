import React, { useState, useEffect, useRef } from 'react';
import useTestStore from '../store/testStore';
import ProgressBar from '../components/ProgressBar';
import Timer from '../components/Timer';
import LoadingSpinner from '../components/LoadingSpinner';
import { motion, AnimatePresence } from 'framer-motion';
import ReportModal from '../components/ReportModal';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { coldarkDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// --- Komponent oceny trudności (spaced repetition) ---
const DifficultyRater = ({ questionId }) => {
    const { rateDifficulty, difficultyRatings, user } = useTestStore();
    if (!user) return null;
    const current = difficultyRatings[questionId];
    const ratings = [
        { key: 'easy',   label: 'Easy',   active: 'border-green-500 text-green-500 bg-green-500/10', hover: 'hover:border-green-500 hover:text-green-500' },
        { key: 'normal', label: 'Normal', active: 'border-yellow-500 text-yellow-500 bg-yellow-500/10', hover: 'hover:border-yellow-500 hover:text-yellow-500' },
        { key: 'hard',   label: 'Hard',   active: 'border-red-500 text-red-500 bg-red-500/10', hover: 'hover:border-red-500 hover:text-red-500' },
    ];
    return (
        <div className="flex items-center justify-center gap-2 mt-4">
            <span className="text-xs text-gray-400 dark:text-gray-500 mr-1">How was it?</span>
            {ratings.map(r => (
                <button
                    key={r.key}
                    onClick={() => rateDifficulty(questionId, r.key)}
                    className={`text-xs px-3 py-1 rounded-full border transition-all ${
                        current === r.key
                            ? r.active + ' font-semibold'
                            : 'border-gray-300 dark:border-gray-600 text-gray-400 ' + r.hover
                    }`}
                >
                    {r.label}
                </button>
            ))}
        </div>
    );
};

// --- Komponent dla pytań otwartych ---
const OpenEndedQuestionUI = () => {
    const {
        currentQuestions,
        currentQuestionIndex,
        checkingQuestionId,
        openQuestionResults,
        nextQuestion,
        setError,
        error: apiError
    } = useTestStore();
    const [userAnswer, setUserAnswer] = useState('');
    const [isSlowGrading, setIsSlowGrading] = useState(false);
    const slowWarningRef = useRef(null);
    const question = currentQuestions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex >= currentQuestions.length - 1;
    const questionResult = openQuestionResults[question.id];
    const isCurrentlyChecking = checkingQuestionId === question.id;
    const isCli = question.type === 'open-cli';
    const isCode = question.type === 'open-code';
    const codeLanguage = isCode && question.gradingCriteria?.includes(':')
        ? question.gradingCriteria.split(':')[0].trim()
        : null;

    useEffect(() => {
        return () => {
            if (slowWarningRef.current) clearTimeout(slowWarningRef.current);
        };
    }, []);

    const handleSubmit = async () => {
        if (!userAnswer.trim() || isCurrentlyChecking || questionResult?.feedback) return;
        setError(null);
        setIsSlowGrading(false);
        if (slowWarningRef.current) clearTimeout(slowWarningRef.current);
        slowWarningRef.current = setTimeout(() => setIsSlowGrading(true), 15000);

        try {
            const taskResponse = await useTestStore.getState().checkOpenAnswer(userAnswer);
            const taskId = taskResponse.task_id;
            if (!taskId) throw new Error("No task ID received from server.");
            useTestStore.getState().startPolling(taskId, question.id);
        } catch (error) {
             useTestStore.getState().setError({ message: error.message || 'Failed to start the grading task.' });
        }
    };

    const handleRequestAI = async () => {
        if (isCurrentlyChecking) return;
        setError(null);
        setIsSlowGrading(false);
        if (slowWarningRef.current) clearTimeout(slowWarningRef.current);
        slowWarningRef.current = setTimeout(() => setIsSlowGrading(true), 15000);
        const answerToRe = questionResult?.userAnswer || userAnswer;
        try {
            const taskResponse = await useTestStore.getState().checkOpenAnswer(answerToRe, true);
            const taskId = taskResponse.task_id;
            if (!taskId) throw new Error("No task ID received from server.");
            useTestStore.getState().startPolling(taskId, question.id);
        } catch (error) {
            useTestStore.getState().setError({ message: error.message || 'Failed to start AI grading.' });
        }
    };

    // Loading view takes priority (covers re-grading state too)
    if (isCurrentlyChecking) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-center">
                <LoadingSpinner />
                <p className="text-lg text-gray-600 dark:text-gray-300 mt-4">Grading your answer with AI...</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">You can continue to the next question.</p>
                {isSlowGrading && (
                    <p className="text-sm text-yellow-500 dark:text-yellow-400 mt-1">This is taking longer than expected...</p>
                )}
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={nextQuestion}
                    className="btn-primary mt-6 py-2 px-8"
                >
                    {isLastQuestion ? "Finish test" : "Next question"}
                </motion.button>
            </div>
        );
    }

    // Result view (shown after grading, including re-grading)
    if (questionResult?.feedback) {
        const autoGradedMethods = ['regex_pass', 'vector_pass', 'vector_fail', 'exact_pass'];
        const isAutoGraded = autoGradedMethods.includes(questionResult.grading_method);
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="text-center">
                <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">Grading result</h3>
                <p className="text-3xl font-bold text-brand-primary mb-2">
                    {questionResult.points_awarded} / {questionResult.maxPoints} pkt
                </p>
                {questionResult.grading_method && (
                    <div className="flex flex-col items-center gap-2 mb-4">
                        <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
                            isAutoGraded
                                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                        }`}>
                            {isAutoGraded ? 'Auto-graded' : 'Graded by AI'}
                        </span>
                        {isAutoGraded && (
                            <button
                                onClick={handleRequestAI}
                                className="text-xs text-gray-500 dark:text-gray-400 hover:text-brand-primary dark:hover:text-brand-primary underline underline-offset-2 transition-colors"
                            >
                                Not sure about the result? Request AI grading
                            </button>
                        )}
                    </div>
                )}
                <div className="text-left bg-gray-100 dark:bg-option-bg p-4 rounded-lg mb-4">
                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Feedback:</h4>
                    <p className="text-gray-600 dark:text-gray-400">{questionResult.feedback}</p>
                </div>
                <DifficultyRater questionId={question.id} />
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={nextQuestion}
                    className="btn-primary mt-4 py-2 px-8 flex items-center justify-center mx-auto"
                >
                    <span>{isLastQuestion ? "View results" : "Next"}</span>
                     <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                </motion.button>
            </motion.div>
        );
    }

    // Domyślny widok do wpisania odpowiedzi
    const baseTextareaClass = "w-full h-40 p-3 rounded-lg bg-gray-100 dark:bg-option-bg border-2 border-gray-300 dark:border-gray-600 focus:border-brand-primary focus:ring-brand-primary transition-colors text-gray-900 dark:text-white";
    return (
         <div className="w-full">
            {isCode && codeLanguage && (
                <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 uppercase tracking-wide">
                        {codeLanguage}
                    </span>
                </div>
            )}
            <textarea
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder={isCli ? "Enter command..." : isCode ? "Write your code here..." : "Type your answer here..."}
                className={`${baseTextareaClass}${(isCli || isCode) ? ' font-mono' : ''}`}
                style={(isCli || isCode) ? { fontFamily: 'monospace' } : undefined}
                spellCheck={isCli || isCode ? false : undefined}
                autoCorrect={isCli || isCode ? "off" : undefined}
                autoCapitalize={isCli || isCode ? "off" : undefined}
                aria-label="Answer field"
            />
            <p className="text-xs text-gray-400 dark:text-gray-500 text-right mt-1">
                {userAnswer.length} {userAnswer.length === 1 ? 'character' : 'characters'}
            </p>
            {apiError && (
                <div className="mt-2 text-center">
                    <p className="text-red-500 text-sm">{apiError.message}</p>
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSubmit}
                        disabled={!userAnswer.trim()}
                        className="btn-primary mt-2 py-1.5 px-6 text-sm"
                    >
                        Try again
                    </motion.button>
                </div>
            )}
            {!apiError && (
                <div className="mt-8 text-center min-h-[52px]">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSubmit}
                        disabled={!userAnswer.trim()}
                        className="btn-primary py-2 px-8"
                    >
                        Check answer
                    </motion.button>
                </div>
            )}
        </div>
    );
};


const TestScreenPage = () => {
    const { 
        currentQuestions, 
        currentQuestionIndex, 
        userAnswers, 
        submitAnswer, 
        nextQuestion, 
        confirmAnswer, 
        timerEnabled,
    } = useTestStore();
    
    const [selection, setSelection] = useState([]);
    const [showFeedback, setShowFeedback] = useState(false);
    const [isReportModalOpen, setIsReportModalOpen] = useState(false);
    const [isReported, setIsReported] = useState(false);
    const question = currentQuestions[currentQuestionIndex];


    const markdownComponents = {
        // 'pre' wraps every fenced code block. Overriding it lets us control
        // the block container independently of whether a language is specified.
        pre({children, ...props}) {
            return (
                <pre {...props} style={{ whiteSpace: 'pre', overflowX: 'auto', maxWidth: '100%', margin: '0.75rem 0' }}>
                    {children}
                </pre>
            );
        },
        // 'code' is called for both inline (`code`) and fenced blocks.
        // In react-markdown v9+, the 'inline' prop was removed. We detect block
        // code by the presence of a language class; no-language fenced blocks
        // are handled by the 'pre' override above (which preserves whitespace).
        code({node: _node, className, children, ...props}) {
            const match = /language-(\w+)/.exec(className || '');
            if (match) {
                return (
                    <SyntaxHighlighter
                        style={coldarkDark}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{ fontSize: '1rem', lineHeight: '1.5', margin: 0 }}
                    >
                        {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                );
            }
            return (
                <code className={className} {...props}>
                    {children}
                </code>
            );
        }
    };

    useEffect(() => {
        if (question) {
            if (question.type === 'single-choice' || question.type === 'multiple-choice') {
                 setSelection(userAnswers[question.id] || []);
            }
            setShowFeedback(false);
        }
        setIsReported(false);
    }, [question, userAnswers]);

    if (!question) {
        return (
            <div className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto p-8 md:p-12 text-center text-gray-800 dark:text-white">
                Loading question...
            </div>
        );
    }

    // --- LOGIKA DLA PYTAŃ ZAMKNIĘTYCH (BEZ ZMIAN) ---
    const handleOptionChange = (optionIndex) => {
        if (showFeedback) return;
        let newSelection;
        if (question.type === 'single-choice') {
            newSelection = [optionIndex];
        } else {
            const selectionSet = new Set(selection);
            if (selectionSet.has(optionIndex)) {
                selectionSet.delete(optionIndex);
            } else {
                selectionSet.add(optionIndex);
            }
            newSelection = Array.from(selectionSet);
        }
        setSelection(newSelection);
        submitAnswer(question.id, newSelection);
    };
    
    const handleConfirm = () => {
        setShowFeedback(true);
        confirmAnswer();
    };

    const handleNext = () => {
        nextQuestion();
    };

    const getOptionClass = (optionIndex) => {
        const baseClasses = 'option-btn w-full text-left p-4 rounded-lg font-medium cursor-pointer';
        const isSelected = selection.includes(optionIndex);

        if (showFeedback) {
            const isCorrectAnswer = question.correctAnswers.includes(optionIndex);
            if (isCorrectAnswer) return `${baseClasses} disabled correct`;
            if (isSelected) return `${baseClasses} disabled incorrect`;
            return `${baseClasses} disabled`;
        }

        return isSelected ? `${baseClasses} option-selected` : baseClasses;
    };
    // --- KONIEC LOGIKI DLA PYTAŃ ZAMKNIĘTYCH ---

    const isLastQuestion = currentQuestionIndex >= currentQuestions.length - 1;
    const isClosedQuestion = question.type === 'single-choice' || question.type === 'multiple-choice';

    return (
        <div className="w-full px-4">
            <div className="relative max-w-3xl mx-auto">
                <motion.div
                    key={currentQuestionIndex}
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -50 }}
                    transition={{ duration: 0.5 }}
                    className="relative w-full"
                >
                    <div className="main-card relative bg-white dark:bg-card-bg w-full p-8 md:p-12">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                                Question {currentQuestionIndex + 1}/{currentQuestions.length}
                            </h2>
                            {timerEnabled && <Timer />}
                        </div>
                        
                        <ProgressBar />
    
                        <div className="my-8 min-h-[96px] flex items-center">
                            <div className="text-2xl md:text-3xl font-medium text-gray-800 dark:text-white leading-snug w-full min-w-0 overflow-x-hidden">
                                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{question.questionText}</ReactMarkdown>
                            </div>
                        </div>
                        
                        {question.image && (
                            <div className="my-4 flex justify-center">
                                <img src={question.image} alt="Question illustration" className="rounded-lg max-w-full h-auto" />
                            </div>
                        )}
                        
                        {isClosedQuestion ? (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {question.options.map((option, index) => (
                                        <motion.div
                                            key={index}
                                            whileHover={{ scale: showFeedback ? 1 : 1.03 }}
                                            whileTap={{ scale: showFeedback ? 1 : 0.98 }}
                                            className={getOptionClass(index)}
                                            onClick={() => handleOptionChange(index)}
                                        >
                                            {option}
                                        </motion.div>
                                    ))}
                                </div>
    
                                <div className="mt-8 text-center min-h-[52px]">
                                    {!showFeedback ? (
                                        <motion.button
                                            whileHover={{ scale: 1.05 }}
                                            whileTap={{ scale: 0.95 }}
                                            onClick={handleConfirm}
                                            disabled={selection.length === 0}
                                            className="btn-primary py-2 px-8"
                                        >
                                            Confirm
                                        </motion.button>
                                    ) : (
                                        <>
                                            <DifficultyRater questionId={question.id} />
                                            <motion.button
                                                whileHover={{ scale: 1.05 }}
                                                whileTap={{ scale: 0.95 }}
                                                onClick={handleNext}
                                                className="btn-primary mt-3 py-2 px-8 flex items-center justify-center mx-auto"
                                            >
                                                <span>{isLastQuestion ? "View results" : "Next"}</span>
                                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                                            </motion.button>
                                        </>
                                    )}
                                </div>
                            </>
                        ) : (
                            <OpenEndedQuestionUI />
                        )}

                        <AnimatePresence>
                            {(showFeedback || !isClosedQuestion) && !isReported && (
                                <motion.button
                                    onClick={() => setIsReportModalOpen(prev => !prev)}
                                    className="absolute bottom-4 left-4 bg-yellow-400 text-gray-800 w-8 h-8 rounded-full shadow-lg flex items-center justify-center z-20"
                                    whileHover={{ scale: 1.1, rotate: 10 }}
                                    whileTap={{ scale: 0.9 }}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 20 }}
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="12" y1="8" x2="12" y2="12"></line>
                                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                    </svg>
                                </motion.button>
                            )}
                        </AnimatePresence>
    
                    </div>
    
                    <AnimatePresence>
                        {isReportModalOpen && (
                            <motion.div
                                layout
                                initial={{ opacity: 0, y: -20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.3 }}
                                className="w-full lg:absolute lg:top-0 lg:right-full lg:w-96 lg:mr-8 mt-8 lg:mt-0"
                            >
                                <ReportModal
                                    question={question}
                                    testId={question.test_id}
                                    aiFeedback={useTestStore.getState().openQuestionResults[question.id]}
                                    userAnswer={
                                        isClosedQuestion
                                            ? selection.map(index => question.options[index])
                                            : useTestStore.getState().openQuestionResults[question.id]?.userAnswer
                                    }
                                    onClose={() => setIsReportModalOpen(false)}
                                    onReportSuccess={() => {
                                        setIsReported(true);
                                        setTimeout(() => setIsReportModalOpen(false), 2000);
                                    }}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
    
                    {isClosedQuestion && showFeedback && (
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="mt-6 md:mt-0 md:absolute md:top-1/2 md:left-full md:-translate-y-1/2 md:ml-8 md:w-80 p-6 bg-gray-200 dark:bg-black/20 border border-gray-300 dark:border-card-border rounded-lg"
                        >
                            <h4 className="font-bold text-gray-800 dark:text-gray-200 text-xl">Explanation:</h4>
                            <div className="prose prose-sm dark:prose-invert mt-2 text-gray-600 dark:text-gray-300">
                                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{question.explanation}</ReactMarkdown>
                            </div>
                        </motion.div>
                    )}
                </motion.div>
            </div>
        </div>
    );
};

export default TestScreenPage;
