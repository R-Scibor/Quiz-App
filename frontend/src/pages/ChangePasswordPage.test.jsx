import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import ChangePasswordPage from './ChangePasswordPage';
import useTestStore from '../store/testStore';

vi.mock('../services/api', () => ({
    getAvailableTests: vi.fn(),
    getQuestions: vi.fn(),
    checkOpenAnswer: vi.fn(),
    getTaskResult: vi.fn(),
    reportIssue: vi.fn(),
    startSession: vi.fn(),
    completeSession: vi.fn(),
    submitAttempts: vi.fn(),
    getUserStats: vi.fn(),
    getStudyQueue: vi.fn(),
    getStudyStats: vi.fn(),
    getTestStats: vi.fn(),
    registerUser: vi.fn(),
    loginUser: vi.fn(),
    logoutUser: vi.fn(),
    changePassword: vi.fn(),
}));

import { changePassword as mockChangePassword } from '../services/api';

describe('ChangePasswordPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        act(() => {
            useTestStore.setState({
                isAuthLoading: false,
                authError: null,
                passwordNotice: null,
                view: 'change-password',
                user: { username: 'alice' },
            });
        });
    });

    test('does not submit when the new passwords differ', () => {
        render(<ChangePasswordPage />);
        fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'old-password' } });
        fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'Quiz-horse-99' } });
        fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'other-password' } });
        fireEvent.click(screen.getByRole('button', { name: 'Update password' }));

        expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match.');
        expect(mockChangePassword).not.toHaveBeenCalled();
    });

    test('submits the current and new password', async () => {
        mockChangePassword.mockResolvedValueOnce({ data: { message: 'Password updated.' } });
        render(<ChangePasswordPage />);
        fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'old-password' } });
        fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'Quiz-horse-99' } });
        fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'Quiz-horse-99' } });
        fireEvent.click(screen.getByRole('button', { name: 'Update password' }));

        expect(await screen.findByRole('status')).toHaveTextContent('Password updated.');
        expect(mockChangePassword).toHaveBeenCalledWith({
            current_password: 'old-password',
            new_password: 'Quiz-horse-99',
        });
    });

    test('back returns home', () => {
        render(<ChangePasswordPage />);
        fireEvent.click(screen.getByRole('button', { name: 'Back' }));
        expect(useTestStore.getState().view).toBe('home');
    });
});