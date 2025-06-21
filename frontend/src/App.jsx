import React, { useEffect } from 'react';
import useTestStore from './store/testStore';
import HomePage from './pages/HomePage';
import TestSetupPage from './pages/TestSetupPage';
import TestScreenPage from './pages/TestScreenPage';
import ResultsPage from './pages/ResultsPage';
import ReviewPage from './pages/ReviewPage';
import ThemeSwitcher from './components/ThemeSwitcher';
import { motion, AnimatePresence } from 'framer-motion';

// Krok 1: Importujemy nowe komponenty tła
import DarkModeBackground from './components/DarkModeBackground';
import LightModeBackground from './components/LightModeBackground';

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
        <div className="relative flex items-center justify-center min-h-screen p-4 transition-colors duration-300 overflow-hidden">
           <AnimatePresence>
             {theme === 'dark' ? <DarkModeBackground /> : <LightModeBackground />}
           </AnimatePresence>
           
           <ThemeSwitcher />
           
           <AnimatePresence mode="wait">
                <motion.div
                    key={view}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -30 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                    className="z-10" // Dodajemy z-index, aby karty były nad tłem
                >
                   {renderView()}
                </motion.div>
           </AnimatePresence>
        </div>
    );
}
export default App;
