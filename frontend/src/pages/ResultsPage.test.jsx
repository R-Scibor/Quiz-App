import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import ResultsPage from './ResultsPage';
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

const q = (id, testId, extra = {}) => ({
    id,
    test_id: testId,
    type: 'single',
    maxPoints: 1,
    correctAnswers: [0],
    ...extra,
});

describe('ResultsPage - per-topic breakdown', () => {
    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            useTestStore.setState({
                view: 'results',
                score: 2,
                availableTests: [],
                studySetupData: null,
                currentQuestions: [],
                userAnswers: {},
                openQuestionResults: {},
                timerEnabled: false,
            });
        });
    });

    afterEach(() => {
        act(() => { useTestStore.getState().resetTest(); });
    });

    test('study mode uses studied_tests titles when availableTests is empty', () => {
        act(() => {
            useTestStore.setState({
                availableTests: [],
                studySetupData: {
                    studied_tests: [
                        { id: 'test-net', title: 'Linux Networking' },
                        { id: 'test-k8s', title: 'Kubernetes' },
                    ],
                },
                currentQuestions: [
                    q('q1', 'test-net'),
                    q('q2', 'test-net'),
                    q('q3', 'test-k8s'),
                ],
                userAnswers: { q1: [0], q2: [1], q3: [0] },
                score: 2,
            });
        });

        render(<ResultsPage />);

        expect(screen.getByText('Per-topic breakdown')).toBeInTheDocument();
        expect(screen.getByText('Linux Networking')).toBeInTheDocument();
        expect(screen.getByText('Kubernetes')).toBeInTheDocument();
        expect(screen.queryByText('Unknown')).not.toBeInTheDocument();
    });

    test('uses question scope when catalog lookups are empty', () => {
        act(() => {
            useTestStore.setState({
                availableTests: [],
                studySetupData: null,
                currentQuestions: [
                    q('q1', 't-a', { scope: 'Medieval Poland' }),
                    q('q2', 't-b', { scope: 'Cell Biology' }),
                ],
                userAnswers: { q1: [0], q2: [0] },
                score: 2,
            });
        });

        render(<ResultsPage />);

        expect(screen.getByText('Medieval Poland')).toBeInTheDocument();
        expect(screen.getByText('Cell Biology')).toBeInTheDocument();
        expect(screen.queryByText('Unknown')).not.toBeInTheDocument();
    });
});
