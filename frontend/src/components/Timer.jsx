import React, { useState, useEffect } from 'react';
import useTestStore from '../store/testStore';

const Timer = () => {
    const { testStartTime, view } = useTestStore();
    const [time, setTime] = useState(0);

    useEffect(() => {
        if (!testStartTime || view !== 'test') { setTime(0); return; }
        const interval = setInterval(() => {
            setTime(Math.floor((new Date() - new Date(testStartTime)) / 1000));
        }, 1000);
        return () => clearInterval(interval);
    }, [testStartTime, view]);

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };
    return <div className="font-mono text-2xl font-bold text-gray-800">{formatTime(time)}</div>;
};
export default Timer;