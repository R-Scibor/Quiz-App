import React from 'react';
import { motion } from 'framer-motion';

const LoadingSpinner = () => {
    return (
        <motion.div
            className="spinner-circle"
            animate={{ rotate: 360 }}
            transition={{
                duration: 1,
                ease: 'linear',
                repeat: Infinity,
            }}
        />
    );
};

export default LoadingSpinner;