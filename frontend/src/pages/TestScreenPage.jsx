import React, { useState, useEffect, useRef } from 'react';
import useTestStore from '../store/testStore';
import ProgressBar from '../components/ProgressBar';
import Timer from '../components/Timer';

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
    const questionTextRef = useRef(null);
    const question = currentQuestions[currentQuestionIndex];

    useEffect(() => {
        if (question) {
            setSelection(userAnswers[question.id] || []);
            setShowFeedback(false);
            const element = questionTextRef.current;
            if (element) {
                element.classList.remove('question-animate-in');
                void element.offsetWidth; 
                element.classList.add('question-animate-in');
            }
        }
    }, [question]);

    if (!question) {
        return (
            <div className="main-card w-full max-w-2xl mx-auto p-8 md:p-12 text-center text-white fade-in">
                Ładowanie pytania...
            </div>
        );
    }

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
        const baseClasses = 'option-btn w-full text-left p-4 rounded-lg font-medium cursor-pointer transition-colors duration-200';
        const isSelected = selection.includes(optionIndex);

        if (showFeedback) {
            const isCorrectAnswer = question.correctAnswers.includes(optionIndex);
            if (isCorrectAnswer) return `${baseClasses} disabled correct`;
            if (isSelected) return `${baseClasses} disabled incorrect`;
            return `${baseClasses} disabled`;
        }

        if (isSelected) {
            // JEDYNA ZMIANA: Używamy naszej nowej, niestandardowej klasy `.option-selected`
            return `${baseClasses} option-selected`;
        }

        return baseClasses;
    };

    const isLastQuestion = currentQuestionIndex >= currentQuestions.length - 1;

    return (
        <div className="main-card w-full max-w-2xl mx-auto p-8 md:p-12 fade-in">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">
                    Pytanie {currentQuestionIndex + 1}/{currentQuestions.length}
                </h2>
                {timerEnabled && <Timer />}
            </div>
            
            <ProgressBar />

            <div className="my-8 min-h-[96px] flex items-center">
                <p ref={questionTextRef} className="text-2xl md:text-3xl font-medium text-white leading-snug">
                    {question.questionText}
                </p>
            </div>
            {question.image && <img src={question.image} alt="Ilustracja do pytania" className="my-4 rounded-lg max-w-full h-auto" />}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {question.options.map((option, index) => (
                    <div
                        key={index}
                        className={getOptionClass(index)}
                        onClick={() => handleOptionChange(index)}
                    >
                        {option}
                    </div>
                ))}
            </div>

            {showFeedback && (
                <div className="mt-6 p-4 bg-black/20 border border-card-border rounded-lg fade-in">
                    <h4 className="font-bold text-gray-200">Wyjaśnienie:</h4>
                    <p className="text-gray-300">{question.explanation}</p>
                </div>
            )}

            <div className="mt-8 text-center min-h-[52px]">
                {!showFeedback ? (
                    <button 
                        onClick={handleConfirm} 
                        disabled={selection.length === 0} 
                        className="btn-primary py-2 px-8"
                    >
                        Zatwierdź
                    </button>
                ) : (
                    <button onClick={handleNext} className="btn-primary py-2 px-8">
                        <span>{isLastQuestion ? "Zobacz wyniki" : "Dalej"}</span>
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                    </button>
                )}
            </div>
        </div>
    );
};

export default TestScreenPage;