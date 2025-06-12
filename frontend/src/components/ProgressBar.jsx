import React from 'react';
import useTestStore from '../store/testStore';

const ProgressBar = () => {
    const { currentQuestionIndex, currentQuestions } = useTestStore();
    const total = currentQuestions.length;
    const current = currentQuestionIndex + 1;
    const progress = total > 0 ? ((current -1) / total) * 100 : 0;
    
    const finalProgress = total > 0 ? (current / total) * 100 : 0;

    return (
        <div className="w-full bg-gray-800 rounded-full h-2.5">
            <div 
                className="bg-gradient-to-r from-brand-secondary to-brand-primary h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${finalProgress}%` }}
            ></div>
        </div>
    );
};
export default ProgressBar;