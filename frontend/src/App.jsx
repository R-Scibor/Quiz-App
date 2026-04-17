import React, { useEffect } from 'react';
import useTestStore from './store/testStore';
import HomePage from './pages/HomePage';
import TestSetupPage from './pages/TestSetupPage';
import TestScreenPage from './pages/TestScreenPage';
import ResultsPage from './pages/ResultsPage';
import ReviewPage from './pages/ReviewPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import StatsPage from './pages/StatsPage';
import StudySetupPage from './pages/StudySetupPage';
import Navbar from './components/Navbar';
import ErrorBoundary from './components/ErrorBoundary';
import { motion, AnimatePresence } from 'framer-motion';

import DarkModeBackground from './components/DarkModeBackground';
import LightModeBackground from './components/LightModeBackground';

function App() {
    const view = useTestStore((state) => state.view);
    const theme = useTestStore((state) => state.theme);
    const initAuth = useTestStore((state) => state.initAuth);

    useEffect(() => {
        const root = window.document.documentElement;
        root.classList.remove('light', 'dark');
        root.classList.add(theme);
    }, [theme]);

    useEffect(() => {
        initAuth();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const renderView = () => {
        switch (view) {
            case 'setup': return <TestSetupPage />;
            case 'test': return <TestScreenPage />;
            case 'results': return <ResultsPage />;
            case 'review': return <ReviewPage />;
            case 'login': return <LoginPage />;
            case 'register': return <RegisterPage />;
            case 'stats': return <StatsPage />;
            case 'study-setup': return <StudySetupPage />;
            case 'home':
            default: return <HomePage />;
        }
    };

    return (
        <ErrorBoundary>
            <div className="relative flex flex-col min-h-screen overflow-hidden transition-colors duration-300">
                <AnimatePresence>
                    {theme === 'dark' ? <DarkModeBackground /> : <LightModeBackground />}
                </AnimatePresence>

                <Navbar />

                <div className="relative z-10 flex-1 flex items-center justify-center p-4">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={view}
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -30 }}
                            transition={{ duration: 0.3, ease: 'easeInOut' }}
                            className="w-full"
                        >
                            {renderView()}
                        </motion.div>
                    </AnimatePresence>
                </div>
            </div>
        </ErrorBoundary>
    );
}
export default App;
