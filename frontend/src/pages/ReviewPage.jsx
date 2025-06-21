import React from 'react';
import useTestStore from '../store/testStore';
import { motion } from 'framer-motion';

// Warianty animacji dla listy pytań
const listVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15
      }
    }
};
  
const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0 }
};

// --- Komponent dla pytania ZAMKNIĘTEGO ---
const ClosedQuestionReview = ({ question, userAnswer }) => {

    const getOptionClass = (optionIndex) => {
        const selected = (userAnswer || []).includes(optionIndex);
        const correct = question.correctAnswers.includes(optionIndex);
        let classes = 'p-4 rounded-lg transition-colors duration-200 border-2';

        if (correct) {
            classes += ' bg-green-100 dark:bg-green-900/50 border-green-500 dark:border-green-600 text-green-800 dark:text-green-200';
        } else if (selected) {
            classes += ' bg-red-100 dark:bg-red-900/50 border-red-500 dark:border-red-600 text-red-800 dark:text-red-200';
        } else {
            classes += ' bg-gray-100 dark:bg-option-bg border-gray-300 dark:border-card-border text-gray-800 dark:text-gray-300';
        }
        return classes;
    };

    return (
        <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                {question.options.map((option, optionIndex) => (
                    <div key={optionIndex} className={getOptionClass(optionIndex)}>
                        {option}
                    </div>
                ))}
            </div>
            {question.explanation && (
                <div className="mt-4 p-4 bg-gray-100 dark:bg-black/20 rounded-lg">
                    <h4 className="font-bold text-gray-700 dark:text-gray-200">Wyjaśnienie:</h4>
                    <p className="text-gray-600 dark:text-gray-300 mt-1">{question.explanation}</p>
                </div>
            )}
        </>
    );
};

// --- Komponent dla pytania OTWARTEGO ---
const OpenQuestionReview = ({ question, result }) => {
    if (!result) {
        return <div className="mt-4 p-4 bg-yellow-100 dark:bg-yellow-900/50 rounded-lg text-yellow-800 dark:text-yellow-200">Brak zapisanej odpowiedzi dla tego pytania.</div>;
    }

    const { userAnswer, points_awarded, feedback } = result;

    // Sprawdzamy, czy wynik jest wyższy niż połowa maksymalnej liczby punktów
    const isScoreHigh = points_awarded >= question.maxPoints / 2;

    // Definiujemy klasy CSS dla obu wariantów
    const successClasses = 'p-4 bg-green-100 dark:bg-green-900/50 rounded-lg mt-2 text-green-800 dark:text-green-200';
    const warningClasses = 'p-4 bg-red-100 dark:bg-red-900/50 rounded-lg mt-2 text-red-800 dark:text-red-200';


    return (
        <div className="space-y-4 mt-4">
            <div>
                <h4 className="font-bold text-gray-700 dark:text-gray-200">Twoja odpowiedź:</h4>
                <p className="p-4 bg-gray-100 dark:bg-option-bg rounded-lg mt-2 text-gray-800 dark:text-gray-300">{userAnswer || "Brak odpowiedzi"}</p>
            </div>
            <div>
                <h4 className="font-bold text-gray-700 dark:text-gray-200">Ocena AI ({points_awarded} / {question.maxPoints} pkt):</h4>
                {/* Używamy operatora trójargumentowego do dynamicznego przypisania klas */}
                <p className={isScoreHigh ? successClasses : warningClasses}>
                    {feedback}
                </p>
            </div>
        </div>
    );
};


// --- GŁÓWNY KOMPONENT STRONY ---
const ReviewPage = () => {
    // Pobieramy ze stanu wszystkie potrzebne dane, które przygotowaliśmy wcześniej
    const { currentQuestions, userAnswers, openQuestionResults, backToResults } = useTestStore();

    return (
        <motion.div className="main-card bg-white dark:bg-card-bg w-full max-w-4xl mx-auto p-8 md:p-12">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-4xl font-bold text-gray-800 dark:text-white">Przegląd odpowiedzi</h1>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={backToResults} 
                    className="btn-primary py-2 px-6 rounded-lg"
                >
                    Wróć do wyników
                </motion.button>
            </div>

            <motion.div 
                className="space-y-10"
                variants={listVariants}
                initial="hidden"
                animate="visible"
            >
                {currentQuestions.map((question, index) => (
                    <motion.div variants={itemVariants} key={question.id} className="border-t border-gray-300 dark:border-card-border pt-6">
                        <p className="text-lg font-semibold text-gray-800 dark:text-white">
                            Pytanie {index + 1}: <span className="font-normal">{question.questionText}</span>
                        </p>
                        
                        {question.image && (
                            <div className="my-4 flex justify-center">
                                <img src={question.image} alt="Ilustracja do pytania" className="rounded-lg max-w-xs h-auto" />
                            </div>
                        )}

                        {/* --- KLUCZOWA LOGIKA WYBORU KOMPONENTU --- */}
                        {question.type === 'open-ended' ? (
                            <OpenQuestionReview 
                                question={question}
                                result={openQuestionResults[question.id]}
                            />
                        ) : (
                            <ClosedQuestionReview 
                                question={question}
                                userAnswer={userAnswers[question.id]}
                            />
                        )}
                    </motion.div>
                ))}
            </motion.div>
        </motion.div>
    );
};

export default ReviewPage;
