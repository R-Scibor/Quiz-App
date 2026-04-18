import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import ReviewPage from './ReviewPage';
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

const OPEN_QUESTION = {
    id: 'q-open',
    questionText: 'Explain what DNS is',
    type: 'open-text',
    gradingCriteria: 'Domain Name System translates hostnames to IP addresses',
    maxPoints: 3,
    test_id: 'test1',
    options: [],
    correctAnswers: [],
};

const CLOSED_QUESTION = {
    id: 'q-closed',
    questionText: 'What color is the sky?',
    type: 'single',
    options: ['Red', 'Blue', 'Green'],
    correctAnswers: [1],
    maxPoints: 1,
    test_id: 'test1',
};

const OPEN_RESULT = {
    userAnswer: 'DNS maps domain names to IP addresses',
    points_awarded: 1,
    feedback: 'Partial credit — missing detail about resolution chain',
    maxPoints: 3,
    grading_method: 'llm',
};

describe('ReviewPage - regrading UI', () => {
    const user = userEvent.setup();

    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            useTestStore.setState({
                view: 'review',
                currentQuestions: [OPEN_QUESTION, CLOSED_QUESTION],
                userAnswers: { 'q-closed': [1] },
                openQuestionResults: { 'q-open': OPEN_RESULT },
                checkingQuestionId: null,
            });
        });
        vi.clearAllMocks();
    });

    afterEach(() => {
        act(() => { useTestStore.getState().resetTest(); });
    });

    test('renders feedback and score for open questions', () => {
        render(<ReviewPage />);

        expect(screen.getByText(OPEN_RESULT.feedback)).toBeInTheDocument();
        expect(screen.getByText(/1 \/ 3 pts/)).toBeInTheDocument();
    });

    test('renders user answer for open questions', () => {
        render(<ReviewPage />);

        expect(screen.getByText(OPEN_RESULT.userAnswer)).toBeInTheDocument();
    });

    test('shows "Re-grade with AI" button for open questions with existing feedback', () => {
        render(<ReviewPage />);

        expect(screen.getByRole('button', { name: /re-grade with ai/i })).toBeInTheDocument();
    });

    test('shows exactly one "Re-grade with AI" button (not shown for closed questions)', () => {
        render(<ReviewPage />);

        expect(screen.getAllByRole('button', { name: /re-grade with ai/i })).toHaveLength(1);
    });

    test('replaces button with spinner while regrading is in progress', () => {
        act(() => {
            useTestStore.setState({ checkingQuestionId: 'q-open' });
        });
        render(<ReviewPage />);

        expect(screen.queryByRole('button', { name: /re-grade with ai/i })).not.toBeInTheDocument();
        expect(screen.getByText(/re-grading with ai/i)).toBeInTheDocument();
    });

    test('shows button again for other open questions while one is regrading', () => {
        const secondOpenQuestion = {
            ...OPEN_QUESTION,
            id: 'q-open-2',
            questionText: 'Explain TCP/IP',
        };
        act(() => {
            useTestStore.setState({
                currentQuestions: [OPEN_QUESTION, secondOpenQuestion, CLOSED_QUESTION],
                openQuestionResults: {
                    'q-open': OPEN_RESULT,
                    'q-open-2': { ...OPEN_RESULT, feedback: 'Different feedback' },
                },
                checkingQuestionId: 'q-open', // only q-open is regrading
            });
        });
        render(<ReviewPage />);

        // q-open-2 should still show the button
        expect(screen.getByRole('button', { name: /re-grade with ai/i })).toBeInTheDocument();
        // q-open shows spinner
        expect(screen.getByText(/re-grading with ai/i)).toBeInTheDocument();
    });

    test('clicking "Re-grade with AI" calls regradeQuestion with correct question id', async () => {
        const regradeQuestionMock = vi.fn().mockResolvedValue({ task_id: 'regrade-42' });
        const startPollingMock = vi.fn();

        act(() => {
            useTestStore.setState({
                regradeQuestion: regradeQuestionMock,
                startPolling: startPollingMock,
            });
        });

        render(<ReviewPage />);
        await user.click(screen.getByRole('button', { name: /re-grade with ai/i }));

        expect(regradeQuestionMock).toHaveBeenCalledWith('q-open');
    });

    test('clicking "Re-grade with AI" calls startPolling with the returned task_id', async () => {
        const regradeQuestionMock = vi.fn().mockResolvedValue({ task_id: 'regrade-42' });
        const startPollingMock = vi.fn();

        act(() => {
            useTestStore.setState({
                regradeQuestion: regradeQuestionMock,
                startPolling: startPollingMock,
            });
        });

        render(<ReviewPage />);
        await user.click(screen.getByRole('button', { name: /re-grade with ai/i }));

        expect(startPollingMock).toHaveBeenCalledWith('regrade-42', 'q-open');
    });

    test('does not call startPolling if regradeQuestion returns no task_id', async () => {
        const regradeQuestionMock = vi.fn().mockResolvedValue(null);
        const startPollingMock = vi.fn();

        act(() => {
            useTestStore.setState({
                regradeQuestion: regradeQuestionMock,
                startPolling: startPollingMock,
            });
        });

        render(<ReviewPage />);
        await user.click(screen.getByRole('button', { name: /re-grade with ai/i }));

        expect(startPollingMock).not.toHaveBeenCalled();
    });

    test('shows fallback message when open question has no result', () => {
        act(() => {
            useTestStore.setState({ openQuestionResults: {} });
        });
        render(<ReviewPage />);

        expect(screen.getByText(/no saved answer/i)).toBeInTheDocument();
    });
});
