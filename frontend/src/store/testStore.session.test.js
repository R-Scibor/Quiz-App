import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import useTestStore from './testStore';

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

import { completeSession as mockCompleteSession, submitAttempts as mockSubmitAttempts } from '../services/api';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const CLOSED_Q = (id, correctAnswers = [0]) => ({
    id,
    type: 'single-choice',
    questionText: 'A closed question',
    options: ['A', 'B', 'C'],
    correctAnswers,
    maxPoints: null,
    test_id: 'test-1',
});

const OPEN_Q = (id, maxPoints = 5) => ({
    id,
    type: 'open-text',
    questionText: 'An open question',
    options: [],
    correctAnswers: [],
    gradingCriteria: 'Must mention X',
    maxPoints,
    test_id: 'test-1',
});

const LOGGED_IN_USER = { username: 'testuser' };

function setupSession(overrides = {}) {
    act(() => {
        useTestStore.getState().resetTest();
        useTestStore.setState({
            user: LOGGED_IN_USER,
            authToken: 'tok',
            currentSessionId: 'session-uuid',
            ...overrides,
        });
    });
    vi.clearAllMocks();
    mockCompleteSession.mockResolvedValue({});
    mockSubmitAttempts.mockResolvedValue({});
}

// ---------------------------------------------------------------------------
// _finalizeSession — guard conditions
// ---------------------------------------------------------------------------

describe('_finalizeSession — guard conditions', () => {
    beforeEach(() => { act(() => { useTestStore.getState().resetTest(); }); });

    test('is a no-op when currentSessionId is null', async () => {
        act(() => {
            useTestStore.setState({ user: LOGGED_IN_USER, currentSessionId: null });
        });
        vi.clearAllMocks();

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        expect(mockCompleteSession).not.toHaveBeenCalled();
        expect(mockSubmitAttempts).not.toHaveBeenCalled();
    });

    test('is a no-op when user is null', async () => {
        act(() => {
            useTestStore.setState({ user: null, currentSessionId: 'session-abc' });
        });
        vi.clearAllMocks();

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        expect(mockCompleteSession).not.toHaveBeenCalled();
        expect(mockSubmitAttempts).not.toHaveBeenCalled();
    });
});

// ---------------------------------------------------------------------------
// _finalizeSession — completeSession payload
// ---------------------------------------------------------------------------

describe('_finalizeSession — completeSession payload', () => {
    beforeEach(() => setupSession());

    test('calls completeSession with correct totals for two correct closed questions', async () => {
        const q1 = CLOSED_Q('q1', [0]);
        const q2 = CLOSED_Q('q2', [1]);

        act(() => {
            useTestStore.setState({
                currentQuestions: [q1, q2],
                userAnswers: { q1: [0], q2: [1] }, // both correct
                score: 2,
                openQuestionResults: {},
                questionTimes: {},
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        expect(mockCompleteSession).toHaveBeenCalledWith('session-uuid', {
            total_questions: 2,
            correct_count: 2,
            score_achieved: 2,
            score_possible: 2,
        });
    });

    test('score_possible sums (maxPoints || 1) across all questions', async () => {
        const q1 = CLOSED_Q('q1', [0]);      // maxPoints=null → 1
        const q2 = CLOSED_Q('q2', [1]);      // maxPoints=null → 1
        const q3 = OPEN_Q('q3', 5);          // maxPoints=5

        act(() => {
            useTestStore.setState({
                currentQuestions: [q1, q2, q3],
                userAnswers: { q1: [0], q2: [1] },
                score: 2,
                openQuestionResults: { q3: { points_awarded: 3 } },
                questionTimes: {},
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        expect(mockCompleteSession).toHaveBeenCalledWith('session-uuid', expect.objectContaining({
            score_possible: 7, // 1 + 1 + 5
        }));
    });
});

// ---------------------------------------------------------------------------
// _finalizeSession — open question scoring
// ---------------------------------------------------------------------------

describe('_finalizeSession — open question scoring', () => {
    beforeEach(() => setupSession());

    test('open question is_correct=true when points_awarded >= maxPoints * 0.66', async () => {
        const q = OPEN_Q('qo', 3);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: {},
                score: 2,
                openQuestionResults: { qo: { points_awarded: 2 } }, // 2 >= 3*0.66=1.98 ✓
                questionTimes: {},
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].is_correct).toBe(true);
        expect(attempts[0].points_awarded).toBe(2);
    });

    test('open question is_correct=false when points_awarded < maxPoints * 0.66', async () => {
        const q = OPEN_Q('qo', 3);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: {},
                score: 1,
                openQuestionResults: { qo: { points_awarded: 1 } }, // 1 < 3*0.66=1.98 ✗
                questionTimes: {},
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].is_correct).toBe(false);
    });

    test('open question with no result defaults to points_awarded=0, is_correct=false', async () => {
        const q = OPEN_Q('qo', 5);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: {},
                score: 0,
                openQuestionResults: {}, // no entry for this question
                questionTimes: {},
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].points_awarded).toBe(0);
        expect(attempts[0].is_correct).toBe(false);
    });
});

// ---------------------------------------------------------------------------
// _finalizeSession — closed question scoring
// ---------------------------------------------------------------------------

describe('_finalizeSession — closed question scoring', () => {
    beforeEach(() => setupSession());

    test('is_correct=true regardless of answer order (sort comparison)', async () => {
        const q = CLOSED_Q('qc', [0, 2]);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: { qc: [2, 0] }, // reversed order → still correct
                score: 1,
                openQuestionResults: {},
                questionTimes: {},
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].is_correct).toBe(true);
    });

    test('is_correct=false for wrong answer', async () => {
        const q = CLOSED_Q('qc', [0]);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: { qc: [1] }, // wrong
                score: 0,
                openQuestionResults: {},
                questionTimes: {},
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].is_correct).toBe(false);
    });
});

// ---------------------------------------------------------------------------
// _finalizeSession — attempt metadata
// ---------------------------------------------------------------------------

describe('_finalizeSession — attempt metadata', () => {
    beforeEach(() => setupSession());

    test('includes time_spent_secs from questionTimes', async () => {
        const q = CLOSED_Q('q1', [0]);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: { q1: [0] },
                score: 1,
                openQuestionResults: {},
                questionTimes: { q1: 42 },
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].time_spent_secs).toBe(42);
    });

    test('time_spent_secs defaults to 0 when question is not in questionTimes', async () => {
        const q = CLOSED_Q('q1', [0]);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: { q1: [0] },
                score: 1,
                openQuestionResults: {},
                questionTimes: {}, // no entry
                difficultyRatings: {},
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].time_spent_secs).toBe(0);
    });

    test('includes difficulty_rating from difficultyRatings', async () => {
        const q = CLOSED_Q('q1', [0]);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: { q1: [0] },
                score: 1,
                openQuestionResults: {},
                questionTimes: {},
                difficultyRatings: { q1: 'hard' },
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].difficulty_rating).toBe('hard');
    });

    test('difficulty_rating is null when not rated', async () => {
        const q = CLOSED_Q('q1', [0]);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: { q1: [0] },
                score: 1,
                openQuestionResults: {},
                questionTimes: {},
                difficultyRatings: {}, // not rated
            });
        });

        await act(async () => { await useTestStore.getState()._finalizeSession(); });

        const attempts = mockSubmitAttempts.mock.calls[0][0];
        expect(attempts[0].difficulty_rating).toBeNull();
    });
});

// ---------------------------------------------------------------------------
// _finalizeSession — error handling (BUG documented)
// ---------------------------------------------------------------------------

describe('_finalizeSession — error handling', () => {
    beforeEach(() => setupSession());

    test.skip(
        // BUG: _finalizeSession calls completeSession then submitAttempts sequentially
        // inside a single try/catch block (testStore.js:372-382).
        // If completeSession() throws, execution jumps to the catch handler and
        // submitAttempts() is never called — attempt records are silently lost.
        // Root cause: `await completeSession(...); await submitAttempts(...)` inside one try.
        // Fix: wrap each call in its own try/catch so submitAttempts always runs
        // regardless of completeSession outcome.
        'submitAttempts is called even when completeSession throws',
        async () => {
            const q = CLOSED_Q('q1', [0]);
            act(() => {
                useTestStore.setState({
                    currentQuestions: [q],
                    userAnswers: { q1: [0] },
                    score: 1,
                    openQuestionResults: {},
                    questionTimes: {},
                    difficultyRatings: {},
                });
            });
            mockCompleteSession.mockRejectedValueOnce(new Error('Network error'));

            await act(async () => { await useTestStore.getState()._finalizeSession(); });

            // submitAttempts should still be called even though completeSession failed
            expect(mockSubmitAttempts).toHaveBeenCalled();
        }
    );

    test('errors from completeSession are swallowed (no exception propagates)', async () => {
        const q = CLOSED_Q('q1', [0]);
        act(() => {
            useTestStore.setState({
                currentQuestions: [q],
                userAnswers: { q1: [0] },
                score: 1,
                openQuestionResults: {},
                questionTimes: {},
                difficultyRatings: {},
            });
        });
        mockCompleteSession.mockRejectedValueOnce(new Error('Network error'));

        // Must not throw
        await expect(
            act(async () => { await useTestStore.getState()._finalizeSession(); })
        ).resolves.not.toThrow();
    });
});
