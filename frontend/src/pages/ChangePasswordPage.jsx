import React, { useState } from 'react';
import useTestStore from '../store/testStore';
import { motion } from 'framer-motion';

const ChangePasswordPage = () => {
    const { changePassword, goToHome, isAuthLoading, authError, passwordNotice } = useTestStore();
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [localError, setLocalError] = useState(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (newPassword !== confirm) {
            setLocalError('Passwords do not match.');
            return;
        }
        setLocalError(null);
        changePassword({ current_password: currentPassword, new_password: newPassword });
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
                <h2 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">Change Password</h2>
                <p className="text-gray-500 dark:text-gray-400 mb-8 text-sm">
                    Enter your current password, then choose a new one.
                </p>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" htmlFor="current-password">
                            Current password
                        </label>
                        <input
                            id="current-password"
                            type="password"
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            required
                            autoFocus
                            autoComplete="current-password"
                            disabled={isAuthLoading}
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-card-border bg-white dark:bg-black/20 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition disabled:opacity-60"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" htmlFor="new-password">
                            New password
                        </label>
                        <input
                            id="new-password"
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            required
                            minLength={8}
                            autoComplete="new-password"
                            disabled={isAuthLoading}
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-card-border bg-white dark:bg-black/20 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition disabled:opacity-60"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" htmlFor="confirm-password">
                            Confirm new password
                        </label>
                        <input
                            id="confirm-password"
                            type="password"
                            value={confirm}
                            onChange={(e) => setConfirm(e.target.value)}
                            required
                            autoComplete="new-password"
                            disabled={isAuthLoading}
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-card-border bg-white dark:bg-black/20 text-gray-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition disabled:opacity-60"
                        />
                    </div>

                    {error && (
                        <p className="text-red-500 text-sm" role="alert">{error}</p>
                    )}
                    {passwordNotice && !error && (
                        <p className="text-emerald-600 dark:text-emerald-400 text-sm" role="status">{passwordNotice}</p>
                    )}

                    <motion.button
                        type="submit"
                        disabled={isAuthLoading}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="btn-primary w-full font-bold py-3 rounded-full text-base shadow-primary hover:shadow-primary-hover transition-all duration-300 disabled:opacity-60"
                    >
                        {isAuthLoading ? 'Updating…' : 'Update password'}
                    </motion.button>
                </form>

                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-card-border">
                    <button
                        type="button"
                        onClick={goToHome}
                        className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                    >
                        Back
                    </button>
                </div>
            </div>
        </motion.div>
    );
};

export default ChangePasswordPage;
