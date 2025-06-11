import React, { useState } from 'react';
import useTestStore from '../store/testStore';
import ProgressBar from '../components/ProgressBar';
import Timer from '../components/Timer';

const TestScreenPage = () => {
    const { currentQuestions, currentQuestionIndex, userAnswers, submitAnswer, nextQuestion, confirmAnswer, timerEnabled } = useTestStore();
    const [showFeedback, setShowFeedback] = useState(false);
    
    const question = currentQuestions[currentQuestionIndex];

    const handleOptionChange = (optionIndex) => {
        if (showFeedback) return;
        const currentSelection = userAnswers[question.id] || [];
        if (question.type === 'single-choice') {
            submitAnswer(question.id, [optionIndex]);
        } else {
            const newSelection = new Set(currentSelection);
            if (newSelection.has(optionIndex)) newSelection.delete(optionIndex);
            else newSelection.add(optionIndex);
            submitAnswer(question.id, Array.from(newSelection));
        }
    };
    
    const handleConfirm = () => { setShowFeedback(true); confirmAnswer(); };
    const handleNext = () => { setShowFeedback(false); nextQuestion(); };

    if (!question) return <div className="text-center p-8">Ładowanie pytania...</div>;

    const getOptionClass = (optionIndex) => {
        if (!showFeedback) return "bg-gray-50 hover:bg-gray-100";
        const userSelection = userAnswers[question.id] || [];
        const isCorrect = question.correctAnswers.includes(optionIndex);
        if (isCorrect) return "bg-green-200 border-green-500";
        if (userSelection.includes(optionIndex) && !isCorrect) return "bg-red-200 border-red-500";
        return "bg-gray-50";
    };

    return (
        <div className="w-full max-w-3xl mx-auto p-8 bg-white rounded-xl shadow-lg">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-700">Pytanie {currentQuestionIndex + 1}</h2>
                {timerEnabled && <Timer />}
            </div>
            <ProgressBar />
            <div className="mt-8">
                <h3 className="text-2xl font-semibold text-gray-800 mb-4">{question.questionText}</h3>
                {question.image && <img src={question.image} alt="Ilustracja do pytania" className="my-4 rounded-lg max-w-full h-auto" />}
                <div className="space-y-3">
                    {question.options.map((option, index) => (
                        <label key={index} className={`flex items-center p-4 rounded-lg border-2 transition-colors cursor-pointer ${getOptionClass(index)}`}>
                             <input type={question.type === 'single-choice' ? 'radio' : 'checkbox'} name={`question-${question.id}`} className="h-5 w-5" checked={(userAnswers[question.id] || []).includes(index)} onChange={() => handleOptionChange(index)} disabled={showFeedback} />
                            <span className="ml-4 text-lg text-gray-800">{option}</span>
                        </label>
                    ))}
                </div>
                {showFeedback && (
                    <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <h4 className="font-bold text-blue-800">Wyjaśnienie:</h4>
                        <p className="text-blue-700">{question.explanation}</p>
                    </div>
                )}
            </div>
            <div className="mt-8 flex justify-end">
                {!showFeedback ? (
                    <button onClick={handleConfirm} disabled={!userAnswers[question.id]?.length} className="bg-green-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-green-700 disabled:bg-gray-400">Zatwierdź</button>
                ) : (
                    <button onClick={handleNext} className="bg-blue-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-blue-700">Następne pytanie</button>
                )}
            </div>
        </div>
    );
};
export default TestScreenPage;
