import React, { useEffect } from 'react';
import useTestStore from './store/testStore';
import HomePage from './pages/HomePage'; // ZMIANA: Importujemy HomePage
import TestSetupPage from './pages/TestSetupPage';
import TestScreenPage from './pages/TestScreenPage';
import ResultsPage from './pages/ResultsPage';
import ReviewPage from './pages/ReviewPage';
import ThemeSwitcher from './components/ThemeSwitcher';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
    const view = useTestStore((state) => state.view);
    const theme = useTestStore((state) => state.theme);

    useEffect(() => {
        const root = window.document.documentElement;
        root.classList.remove('light', 'dark');
        root.classList.add(theme);
    }, [theme]);
    
    const renderView = () => {
        switch (view) {
            case 'setup': return <TestSetupPage />;
            case 'test': return <TestScreenPage />;
            case 'results': return <ResultsPage />;
            case 'review': return <ReviewPage />;
            case 'home':
            default: return <HomePage />;
        }
    };

    return (
        <div className="relative flex items-center justify-center min-h-screen p-4 bg-gray-100 dark:bg-brand-background transition-colors duration-300 overflow-hidden">
           <ThemeSwitcher />
           
           <AnimatePresence mode="wait">
                <motion.div
                    key={view}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -30 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                >
                   {renderView()}
                </motion.div>
           </AnimatePresence>
        </div>
    );
}
export default App;
