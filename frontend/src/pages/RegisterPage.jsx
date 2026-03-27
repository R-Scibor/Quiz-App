import React, { useState } from 'react';
import useTestStore from '../store/testStore';
import { motion } from 'framer-motion';

const RegisterPage = () => {
    const { register, goToLogin, resetTest, isAuthLoading, authError } = useTestStore();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [localError, setLocalError] = useState(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (password !== confirm) {
            setLocalError('Passwords do not match.');
            return;
        }
        setLocalError(null);
        register({ username, password });
    };

    const error = localError || (authError ? authError.message : null);

    return (
        <motion.div
            className="main-card bg-white dark:bg-card-bg w-full max-w-md mx-auto rounded-2xl shadow-2xl overflow-hidden"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
        >
            <div className="p-8 md:p-12">
                <h2 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">Create Account</h2>
                <p className="text-gray-500 dark:text-gray-400 mb-8 text-sm">Pick a username and password to get started.</p>

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
                            Password <span className="text-gray-400 font-normal">(min. 6 characters)</span>
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            minLength={6}
                            disabled={isAuthLoading}
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-card-border bg-white dark:bg-black/20 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition disabled:opacity-60"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Confirm Password
                        </label>
                        <input
                            type="password"
                            value={confirm}
                            onChange={(e) => setConfirm(e.target.value)}
                            required
                            disabled={isAuthLoading}
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-card-border bg-white dark:bg-black/20 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition disabled:opacity-60"
                        />
                    </div>

                    {error && (
                        <p className="text-red-500 text-sm">{error}</p>
                    )}

                    <motion.button
                        type="submit"
                        disabled={isAuthLoading}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="btn-primary w-full font-bold py-3 rounded-full text-base shadow-primary hover:shadow-primary-hover transition-all duration-300 disabled:opacity-60"
                    >
                        {isAuthLoading ? 'Creating account…' : 'Register'}
                    </motion.button>
                </form>

                <div className="mt-6 flex flex-col sm:flex-row gap-3 pt-6 border-t border-gray-200 dark:border-card-border">
                    <button
                        onClick={goToLogin}
                        className="text-sm text-indigo-500 hover:underline"
                    >
                        Already have an account? Sign in
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

export default RegisterPage;
