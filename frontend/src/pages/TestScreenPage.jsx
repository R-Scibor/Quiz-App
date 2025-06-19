import React, { useState, useEffect, useRef } from 'react';
import useTestStore from '../store/testStore';
import ProgressBar from '../components/ProgressBar';
import Timer from '../components/Timer';
import { motion, AnimatePresence } from 'framer-motion';

// --- Komponent dla pytań otwartych ---
const OpenEndedQuestionUI = () => {
    const {
        currentQuestions,
        currentQuestionIndex,
        checkOpenAnswer,
        isCheckingAnswer,
        lastAnswerFeedback,
        nextQuestion,
        error: apiError // zmiana nazwy, aby uniknąć konfliktu
    } = useTestStore();
    const [userAnswer, setUserAnswer] = useState('');
    const question = currentQuestions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex >= currentQuestions.length - 1;


    const handleSubmit = () => {
        if (userAnswer.trim()) {
            checkOpenAnswer(userAnswer);
        }
    };
    
    // Widok po ocenie odpowiedzi przez AI
    if (lastAnswerFeedback) {
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="text-center">
                <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-2">Wynik oceny</h3>
                {/* POPRAWKA: Naprawiono literówkę z 'lastAnswerfeedback' na 'lastAnswerFeedback' */}
                <p className="text-3xl font-bold text-brand-primary mb-4">
                    {lastAnswerFeedback.points_awarded} / {lastAnswerFeedback.maxPoints} pkt
                </p>
                <div className="text-left bg-gray-100 dark:bg-option-bg p-4 rounded-lg mb-6">
                    <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Feedback:</h4>
                    <p className="text-gray-600 dark:text-gray-400">{lastAnswerFeedback.feedback}</p>
                </div>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={nextQuestion}
                    className="btn-primary py-2 px-8 flex items-center justify-center mx-auto"
                >
                    <span>{isLastQuestion ? "Zobacz wyniki" : "Dalej"}</span>
                     <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                </motion.button>
            </motion.div>
        );
    }
    
    // Widok ładowania podczas sprawdzania
    if (isCheckingAnswer) {
        return (
            <div className="flex flex-col items-center justify-center p-8 text-center">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-16 h-16 border-4 border-t-brand-primary border-gray-200 dark:border-gray-600 rounded-full mb-4"
                />
                <p className="text-lg text-gray-600 dark:text-gray-300">Ocenianie odpowiedzi przez AI...</p>
            </div>
        );
    }

    // Domyślny widok do wpisania odpowiedzi
    return (
         <div className="w-full">
            <textarea
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                placeholder="Wpisz swoją odpowiedź tutaj..."
                className="w-full h-40 p-3 rounded-lg bg-gray-100 dark:bg-option-bg border-2 border-gray-300 dark:border-gray-600 focus:border-brand-primary focus:ring-brand-primary transition-colors"
                aria-label="Pole odpowiedzi"
            />
            {apiError && <p className="text-red-500 text-sm mt-2 text-center">{apiError}</p>}
            <div className="mt-8 text-center min-h-[52px]">
                 <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleSubmit}
                    disabled={!userAnswer.trim()}
                    className="btn-primary py-2 px-8"
                >
                    Sprawdź odpowiedź
                </motion.button>
            </div>
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
    const question = currentQuestions[currentQuestionIndex];

    useEffect(() => {
        if (question) {
            // Dla pytań zamkniętych, ustawiamy selection z userAnswers
            if (question.type === 'single-choice' || question.type === 'multiple-choice') {
                 setSelection(userAnswers[question.id] || []);
            }
            setShowFeedback(false);
        }
    }, [question, userAnswers]);

    if (!question) {
        return (
            <div className="main-card bg-white dark:bg-card-bg w-full max-w-2xl mx-auto p-8 md:p-12 text-center text-gray-800 dark:text-white">
                Ładowanie pytania...
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
         <motion.div 
            key={currentQuestionIndex} 
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.5 }}
            className="relative w-full max-w-2xl mx-auto px-4"
        >
            <div className="main-card bg-white dark:bg-card-bg w-full p-8 md:p-12">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                        Pytanie {currentQuestionIndex + 1}/{currentQuestions.length}
                    </h2>
                    {timerEnabled && <Timer />}
                </div>
                
                <ProgressBar />

                <div className="my-8 min-h-[96px] flex items-center">
                    {/* POPRAWKA: Przywrócono 'question.questionText' z oryginalnego pliku */}
                    <p className="text-2xl md:text-3xl font-medium text-gray-800 dark:text-white leading-snug">
                         {question.questionText}
                    </p>
                </div>
                
                {question.image && (
                    <div className="my-4 flex justify-center">
                        <img src={question.image} alt="Ilustracja do pytania" className="rounded-lg max-w-full h-auto" />
                    </div>
                )}
                
                {/* RENDEROWANIE WARUNKOWE */}
                {isClosedQuestion ? (
                    <>
                        {/* UI dla pytań zamkniętych (bez zmian) */}
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
                                    Zatwierdź
                                </motion.button>
                            ) : (
                                <motion.button 
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={handleNext} 
                                    className="btn-primary py-2 px-8 flex items-center justify-center mx-auto"
                                >
                                    <span>{isLastQuestion ? "Zobacz wyniki" : "Dalej"}</span>
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                                </motion.button>
                            )}
                        </div>
                    </>
                ) : (
                    // Nowe UI dla pytań otwartych
                    <OpenEndedQuestionUI />
                )}

            </div>

            {/* Panel z wyjaśnieniem (tylko dla pytań zamkniętych po odpowiedzi) */}
            {isClosedQuestion && showFeedback && (
                <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="mt-6 md:mt-0 md:absolute md:top-1/2 md:left-full md:-translate-y-1/2 md:ml-8 md:w-80 p-6 bg-gray-200 dark:bg-black/20 border border-gray-300 dark:border-card-border rounded-lg"
                >
                    <h4 className="font-bold text-gray-800 dark:text-gray-200 text-xl">Wyjaśnienie:</h4>
                    <p className="text-gray-600 dark:text-gray-300 mt-2">{question.explanation}</p>
                </motion.div>
            )}
        </motion.div>
    );
};

export default TestScreenPage;
