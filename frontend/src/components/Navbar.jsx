import React from 'react';
import useTestStore from '../store/testStore';

const SunIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
    </svg>
);

const MoonIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
    </svg>
);

const Navbar = () => {
    const {
        user, studyQueueCount, theme,
        goToHome, goToStats, goToStudySetup, goToLogin, goToRegister, logout, toggleTheme,
    } = useTestStore();

    const handleStudyClick = () => {
        goToStudySetup();
    };

    return (
        <nav className="sticky top-0 z-20 w-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200/60 dark:border-gray-700/60">
            <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
                {/* Logo */}
                <button
                    onClick={goToHome}
                    className="flex items-center gap-2 font-bold text-lg text-gray-800 dark:text-white hover:text-brand-primary dark:hover:text-brand-primary transition-colors"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                    </svg>
                    <span className="hidden sm:inline">Quiz App</span>
                </button>

                {/* Right side */}
                <div className="flex items-center gap-2">
                    {user ? (
                        <>
                            {/* Stats */}
                            <button
                                onClick={goToStats}
                                className="text-sm px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            >
                                Stats
                            </button>

                            {/* Study mode with badge */}
                            <button
                                onClick={handleStudyClick}
                                className="relative text-sm px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            >
                                Study
                                {studyQueueCount > 0 && (
                                    <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center text-[10px] font-bold bg-brand-primary text-white rounded-full px-1">
                                        {studyQueueCount > 99 ? '99+' : studyQueueCount}
                                    </span>
                                )}
                            </button>

                            {/* Username chip */}
                            <span className="hidden sm:inline-block text-xs px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-medium">
                                {user.username}
                            </span>

                            {/* Sign out */}
                            <button
                                onClick={logout}
                                className="text-sm px-3 py-1.5 rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            >
                                Sign out
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={goToLogin}
                                className="text-sm px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                            >
                                Sign in
                            </button>
                            <button
                                onClick={goToRegister}
                                className="text-sm px-3 py-1.5 rounded-lg bg-brand-primary text-white hover:opacity-90 transition-opacity"
                            >
                                Register
                            </button>
                        </>
                    )}

                    {/* Theme toggle */}
                    <button
                        onClick={toggleTheme}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                        aria-label="Toggle theme"
                    >
                        {theme === 'light' ? <MoonIcon /> : <SunIcon />}
                    </button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
