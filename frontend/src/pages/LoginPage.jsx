import React, { useState } from 'react';
import useTestStore from '../store/testStore';
import { motion } from 'framer-motion';

const LoginPage = () => {
    const { login, goToRegister, resetTest, isAuthLoading, authError } = useTestStore();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        login({ username, password });
    };

    return (
        <motion.div
            className="main-card bg-white dark:bg-card-bg w-full max-w-md mx-auto rounded-2xl shadow-2xl overflow-hidden"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
        >
            <div className="p-8 md:p-12">
                <h2 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">Sign In</h2>
                <p className={`mb-8 text-sm ${authError?.code === 'SESSION_EXPIRED' ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'}`}>
                    {authError?.code === 'SESSION_EXPIRED'
                        ? authError.message
                        : 'Welcome back — enter your credentials to continue.'}
                </p>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Username
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            autoFocus
                            disabled={isAuthLoading}
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-card-border bg-white dark:bg-black/20 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition disabled:opacity-60"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={isAuthLoading}
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-card-border bg-white dark:bg-black/20 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition disabled:opacity-60"
                        />
                    </div>

                    {authError && authError.code !== 'SESSION_EXPIRED' && (
                        <p className="text-red-500 text-sm">{authError.message}</p>
                    )}

                    <motion.button
                        type="submit"
                        disabled={isAuthLoading}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="btn-primary w-full font-bold py-3 rounded-full text-base shadow-primary hover:shadow-primary-hover transition-all duration-300 disabled:opacity-60"
                    >
                        {isAuthLoading ? 'Signing in…' : 'Sign In'}
                    </motion.button>
                </form>

                <div className="mt-6 flex flex-col sm:flex-row gap-3 pt-6 border-t border-gray-200 dark:border-card-border">
                    <button
                        onClick={goToRegister}
                        className="text-sm text-indigo-500 hover:underline"
                    >
                        No account? Register
                    </button>
                    <button
                        onClick={resetTest}
                        className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 sm:ml-auto"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </motion.div>
    );
};

export default LoginPage;
