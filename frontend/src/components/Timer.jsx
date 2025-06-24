import React, { useState, useEffect } from 'react';
import useTestStore from '../store/testStore';

const Timer = () => {
    const { testStartTime, view, isTimerRunning, questionStartTime, totalTimeSpent } = useTestStore();
    const [time, setTime] = useState(0); // This will now represent the accumulated time

    useEffect(() => {
        let interval;
        if (testStartTime && view === 'test' && isTimerRunning && questionStartTime) {
            // Immediately set the time to avoid the 00:00 flicker
            const initialTimeElapsed = Math.floor((new Date() - new Date(questionStartTime)) / 1000);
            setTime(totalTimeSpent + initialTimeElapsed);

            interval = setInterval(() => {
                const currentTimeElapsed = Math.floor((new Date() - new Date(questionStartTime)) / 1000);
                setTime(totalTimeSpent + currentTimeElapsed);
            }, 1000);
        } else {
            // If timer is not running or not in test view, ensure time reflects totalTimeSpent
            setTime(totalTimeSpent);
        }
        return () => clearInterval(interval);
    }, [testStartTime, view, isTimerRunning, questionStartTime, totalTimeSpent]);

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };
    return <div className="font-mono text-2xl font-bold text-gray-800">{formatTime(time)}</div>;
};
export default Timer;