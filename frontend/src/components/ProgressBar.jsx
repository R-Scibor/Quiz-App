import React from 'react';
import useTestStore from '../store/testStore';

const ProgressBar = () => {
    const { currentQuestionIndex, currentQuestions } = useTestStore();
    const total = currentQuestions.length;
    const current = currentQuestionIndex + 1;
    const progress = total > 0 ? (current / total) * 100 : 0;
    return (
        <div className="w-full bg-gray-200 rounded-full h-4 my-4">
            <div
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{ width: `${progress}%` }}
            ></div>
            <p className="text-center text-sm font-medium text-gray-700 mt-1">{`Pytanie ${current} z ${total}`}</p>
        </div>
    );
};
export default ProgressBar;