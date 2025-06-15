import React from 'react';
import useTestStore from '../store/testStore';
import { motion } from 'framer-motion';

const HomePage = () => {
    const goToSetup = useTestStore((state) => state.goToSetup);

    // Warianty animacji dla kontenera i jego dzieci
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                delayChildren: 0.3,
                staggerChildren: 0.2
            }
        }
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1
        }
    };

    return (
        <motion.div 
            className="main-card bg-white dark:bg-card-bg w-full max-w-5xl mx-auto rounded-2xl shadow-2xl overflow-hidden"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
        >
            <div className="md:flex">
                {/* === Lewa kolumna - Branding === */}
                <div className="md:w-5/12 p-8 md:p-12 bg-gray-50 dark:bg-black/20 flex flex-col justify-center items-center text-center">
                    <motion.img 
                        src="/public/icon.png" 
                        alt="Quiz App Icon" 
                        className="w-32 h-32"
                        initial={{ rotate: -180, scale: 0 }}
                        animate={{ rotate: 0, scale: 1 }}
                        transition={{ type: 'spring', stiffness: 150, damping: 20, delay: 0.2 }}
                    />
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-800 dark:text-white mt-4">
                        Quiz App
                    </h1>
                    <p className="text-md text-gray-500 dark:text-gray-400 mt-2">
                        Platforma do sprawdzania wiedzy
                    </p>
                </div>

                {/* === Prawa kolumna - Akcje i Informacje === */}
                <motion.div 
                    className="md:w-7/12 p-8 md:p-12"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.h2 variants={itemVariants} className="text-3xl font-bold text-gray-800 dark:text-white">
                        Gotowy na wyzwanie?
                    </motion.h2>

                    <motion.p variants={itemVariants} className="text-lg text-gray-600 dark:text-gray-300 mt-2 mb-8">
                        Kliknij przycisk poniżej, aby skonfigurować i rozpocząć swój personalizowany test.
                    </motion.p>
                    
                    <motion.div variants={itemVariants}>
                        <motion.button
                            whileHover={{ scale: 1.03, y: -2 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={goToSetup}
                            className="btn-primary w-full sm:w-auto font-bold py-3 px-10 rounded-full text-lg shadow-primary hover:shadow-primary-hover transition-all duration-300 ease-in-out"
                        >
                            Rozpocznij Quiz
                        </motion.button>
                    </motion.div>
                    
                    <motion.div variants={itemVariants} className="mt-12 pt-6 border-t border-gray-200 dark:border-card-border">
                        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-400 mb-2">O Projekcie</h3>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                            Aplikacja stworzona przy użyciu React, Zustand, Framer Motion, Tailwind CSS oraz Django REST Framework.
                        </p>
                    </motion.div>
                </motion.div>
            </div>
        </motion.div>
    );
};

export default HomePage;
