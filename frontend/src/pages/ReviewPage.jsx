import React from 'react';
import useTestStore from '../store/testStore';

const ReviewPage = () => {
    const { currentQuestions, userAnswers, backToResults } = useTestStore();

    const getOptionClass = (question, optionIndex) => {
        const userAnswer = userAnswers[question.id] || [];
        const isSelected = userAnswer.includes(optionIndex);
        const isCorrect = question.correctAnswers.includes(optionIndex);

        let classes = 'p-4 rounded-lg transition-colors duration-200 border-2';

        if (isCorrect) {
            classes += ' bg-green-100 dark:bg-green-900/50 border-green-500 dark:border-green-600 text-green-800 dark:text-green-200';
        } else if (isSelected) {
            classes += ' bg-red-100 dark:bg-red-900/50 border-red-500 dark:border-red-600 text-red-800 dark:text-red-200';
        } else {
            classes += ' bg-gray-100 dark:bg-option-bg border-gray-300 dark:border-card-border text-gray-800 dark:text-gray-300';
        }
        
        return classes;
    };

    return (
        <div className="main-card bg-white dark:bg-card-bg w-full max-w-4xl mx-auto p-8 md:p-12 fade-in">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-4xl font-bold text-gray-800 dark:text-white">Przegląd odpowiedzi</h1>
                {/* ZMIANA: Zmieniono 'btn-secondary' na 'btn-primary' dla spójności */}
                <button onClick={backToResults} className="btn-primary py-2 px-6 rounded-lg">
                    Wróć do wyników
                </button>
            </div>

            <div className="space-y-10">
                {currentQuestions.map((question, index) => (
                    <div key={question.id} className="border-t border-gray-300 dark:border-card-border pt-6">
                        <p className="text-lg font-semibold text-gray-800 dark:text-white">
                            Pytanie {index + 1}: <span className="font-normal">{question.questionText}</span>
                        </p>
                        
                        {question.image && (
                            <div className="my-4 flex justify-center">
                                <img src={question.image} alt="Ilustracja do pytania" className="rounded-lg max-w-xs h-auto" />
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                            {question.options.map((option, optionIndex) => (
                                <div key={optionIndex} className={getOptionClass(question, optionIndex)}>
                                    {option}
                                </div>
                            ))}
                        </div>

                        <div className="mt-4 p-4 bg-gray-100 dark:bg-black/20 rounded-lg">
                            <h4 className="font-bold text-gray-700 dark:text-gray-200">Wyjaśnienie:</h4>
                            <p className="text-gray-600 dark:text-gray-300 mt-1">{question.explanation}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ReviewPage;
