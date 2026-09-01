import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import StudySetupPage from './StudySetupPage';
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
}));

const SETUP_DATA = {
    due_count: 2,
    struggling_count: 1,
    new_count: 4,
    mastered_count: 0,
    total_queued: 7,
    studied_tests: [{ id: 't1', title: 'Topic A' }],
};

describe('StudySetupPage', () => {
    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            useTestStore.setState({
                user: { username: 'tester' },
                studySetupData: SETUP_DATA,
                view: 'study-setup',
                error: null,
            });
        });
    });

    test('renders queue breakdown', () => {
        render(<StudySetupPage />);
        expect(screen.getByRole('heading', { name: /Study Mode/i })).toBeInTheDocument();
        expect(screen.getByText('Due')).toBeInTheDocument();
        expect(screen.getByText('Struggling')).toBeInTheDocument();
    });

    test('shows the empty-queue error from the store', () => {
        act(() => {
            useTestStore.setState({
                error: {
                    message: 'No questions in your study queue right now.',
                    code: 'EMPTY_QUEUE',
                },
            });
        });
        render(<StudySetupPage />);
        expect(screen.getByText(/No questions in your study queue right now/i)).toBeInTheDocument();
    });
});
