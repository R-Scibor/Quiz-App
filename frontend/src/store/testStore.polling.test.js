import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
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

import { getTaskResult as mockGetTaskResult, checkOpenAnswer as mockCheckOpenAnswer } from '../services/api';

const MOCK_QUESTION = {
    id: 'q1',
    questionText: 'Explain DNS',
    type: 'open-text',
    gradingCriteria: 'Domain Name System',
    maxPoints: 3,
    test_id: 'test1',
    options: [],
    correctAnswers: [],
};

const MOCK_FEEDBACK = {
    score: 2,
    feedback: 'Good answer',
    grading_method: 'llm',
    max_points: 3,
    vector_score: null,
    latency_ms: 1000,
};

// ---------------------------------------------------------------------------
// startPolling
// ---------------------------------------------------------------------------

describe('useTestStore - startPolling', () => {
    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            useTestStore.setState({
                currentQuestions: [MOCK_QUESTION],
                openQuestionResults: {
                    q1: { userAnswer: 'DNS is Domain Name System', points_awarded: 0 },
                },
                checkingQuestionId: 'q1',
            });
        });
        vi.useFakeTimers();
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.useRealTimers();
        act(() => { useTestStore.getState().resetTest(); });
    });

    test('tracks interval in activePolls immediately after call', () => {
        mockGetTaskResult.mockResolvedValue({ data: { status: 'PENDING', data: null } });

        act(() => {
            useTestStore.getState().startPolling('task-abc', 'q1');
        });

        expect(useTestStore.getState().activePolls['task-abc']).toBeDefined();
    });

    test('on SUCCESS: updates openQuestionResults and clears poll and checkingQuestionId', async () => {
        mockGetTaskResult
            .mockResolvedValueOnce({ data: { status: 'PENDING', data: null } })
            .mockResolvedValueOnce({ data: { status: 'SUCCESS', data: MOCK_FEEDBACK } });

        act(() => { useTestStore.getState().startPolling('task-ok', 'q1'); });

        await act(async () => { await vi.advanceTimersByTimeAsync(2000); }); // PENDING
        expect(useTestStore.getState().openQuestionResults['q1'].feedback).toBeUndefined();

        await act(async () => { await vi.advanceTimersByTimeAsync(2000); }); // SUCCESS

        const state = useTestStore.getState();
        expect(state.openQuestionResults['q1'].feedback).toBe('Good answer');
        expect(state.openQuestionResults['q1'].points_awarded).toBe(2);
        expect(state.activePolls['task-ok']).toBeUndefined();
        expect(state.checkingQuestionId).toBeNull();
    });

    test('on FAILURE status: calls setError and clears poll', async () => {
        mockGetTaskResult.mockResolvedValueOnce({ data: { status: 'FAILURE', data: 'Grading failed' } });

        act(() => { useTestStore.getState().startPolling('task-fail', 'q1'); });
        await act(async () => { await vi.advanceTimersByTimeAsync(2000); });

        const state = useTestStore.getState();
        expect(state.error).toBeTruthy();
        expect(state.activePolls['task-fail']).toBeUndefined();
        expect(state.checkingQuestionId).toBeNull();
    });

    test('on network error: calls setError and clears poll', async () => {
        mockGetTaskResult.mockRejectedValueOnce(new Error('Network failure'));

        act(() => { useTestStore.getState().startPolling('task-net', 'q1'); });
        await act(async () => { await vi.advanceTimersByTimeAsync(2000); });

        const state = useTestStore.getState();
        expect(state.error).toBeTruthy();
        expect(state.activePolls['task-net']).toBeUndefined();
    });

    test('times out after 60 retries, calls setError with timeout message, and calls API exactly 60 times', async () => {
        mockGetTaskResult.mockResolvedValue({ data: { status: 'PENDING', data: null } });

        act(() => { useTestStore.getState().startPolling('task-timeout', 'q1'); });

        // 60 retries fire at 2s each; the 61st tick triggers the timeout guard
        await act(async () => { await vi.advanceTimersByTimeAsync(61 * 2000 + 100); });

        const state = useTestStore.getState();
        expect(state.error?.message).toMatch(/timed out/i);
        expect(state.activePolls['task-timeout']).toBeUndefined();
        expect(mockGetTaskResult).toHaveBeenCalledTimes(60);
    });
});

// ---------------------------------------------------------------------------
// checkOpenAnswer guard — scoped to current question only
// ---------------------------------------------------------------------------

describe('useTestStore - checkOpenAnswer guard (scoped to question)', () => {
    const QUESTION_B = {
        id: 'q2',
        questionText: 'Explain TCP',
        type: 'open-text',
        gradingCriteria: 'Transmission Control Protocol',
        maxPoints: 2,
        test_id: 'test1',
    };

    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            useTestStore.setState({
                currentQuestions: [MOCK_QUESTION, QUESTION_B],
                currentQuestionIndex: 0,
            });
        });
        vi.clearAllMocks();
    });

    afterEach(() => {
        act(() => { useTestStore.getState().resetTest(); });
    });

    test('blocks re-submission of the same question that is currently being graded', async () => {
        act(() => {
            useTestStore.setState({ checkingQuestionId: 'q1', currentQuestionIndex: 0 });
        });

        let result;
        await act(async () => {
            result = await useTestStore.getState().checkOpenAnswer('some answer');
        });

        expect(result.task_id).toBeNull();
        expect(mockCheckOpenAnswer).not.toHaveBeenCalled();
    });

    test('allows submitting a different question while another is being graded', async () => {
        // q1 is grading in the background; user has moved to q2
        act(() => {
            useTestStore.setState({ checkingQuestionId: 'q1', currentQuestionIndex: 1 });
        });

        mockCheckOpenAnswer.mockResolvedValue({ data: { task_id: 'task-q2' } });

        let result;
        await act(async () => {
            result = await useTestStore.getState().checkOpenAnswer('TCP answer');
        });

        expect(result.task_id).toBe('task-q2');
        expect(mockCheckOpenAnswer).toHaveBeenCalledOnce();
        // q1 is still being graded; q2 is now also grading
        expect(useTestStore.getState().checkingQuestionId).toBe('q2');
    });
});

// ---------------------------------------------------------------------------
// regradeQuestion
// ---------------------------------------------------------------------------

describe('useTestStore - regradeQuestion', () => {
    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            useTestStore.setState({
                currentQuestions: [MOCK_QUESTION],
                openQuestionResults: {
                    q1: {
                        userAnswer: 'DNS stands for Domain Name System',
                        points_awarded: 1,
                        feedback: 'Partial credit',
                        grading_method: 'llm',
                    },
                },
            });
        });
        vi.clearAllMocks();
    });

    afterEach(() => {
        act(() => { useTestStore.getState().resetTest(); });
    });

    test('sets checkingQuestionId, calls API with forceAI:true, and returns task_id', async () => {
        mockCheckOpenAnswer.mockResolvedValue({ data: { task_id: 'regrade-1' } });

        let result;
        await act(async () => {
            result = await useTestStore.getState().regradeQuestion('q1');
        });

        expect(useTestStore.getState().checkingQuestionId).toBe('q1');
        expect(mockCheckOpenAnswer).toHaveBeenCalledWith(expect.objectContaining({
            questionText: MOCK_QUESTION.questionText,
            userAnswer: 'DNS stands for Domain Name System',
            gradingCriteria: MOCK_QUESTION.gradingCriteria,
            maxPoints: MOCK_QUESTION.maxPoints,
            questionType: MOCK_QUESTION.type,
            forceAI: true,
        }));
        expect(result.task_id).toBe('regrade-1');
    });

    test('returns null without calling API if no stored answer exists', async () => {
        act(() => {
            useTestStore.setState({ openQuestionResults: {} });
        });

        let result;
        await act(async () => {
            result = await useTestStore.getState().regradeQuestion('q1');
        });

        expect(result).toBeNull();
        expect(mockCheckOpenAnswer).not.toHaveBeenCalled();
    });

    test('returns null without calling API if question id is not in currentQuestions', async () => {
        let result;
        await act(async () => {
            result = await useTestStore.getState().regradeQuestion('nonexistent');
        });

        expect(result).toBeNull();
        expect(mockCheckOpenAnswer).not.toHaveBeenCalled();
    });
});

// ---------------------------------------------------------------------------
// resetTest / retryTest cancel active polls
// ---------------------------------------------------------------------------

describe('useTestStore - resetTest and retryTest cancel active polls', () => {
    beforeEach(() => {
        act(() => { useTestStore.getState().resetTest(); });
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        act(() => { useTestStore.getState().resetTest(); });
    });

    test('resetTest calls clearInterval for each active poll and empties activePolls', () => {
        const fakeInterval = setInterval(() => {}, 10000);
        const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval');

        act(() => {
            useTestStore.setState({ activePolls: { 'ghost-task': fakeInterval } });
        });
        expect(useTestStore.getState().activePolls['ghost-task']).toBeDefined();

        act(() => { useTestStore.getState().resetTest(); });

        // Fake timers may pass extra internal args — check only that our interval was the first arg of some call
        const wasCancelled = clearIntervalSpy.mock.calls.some(args => args[0] === fakeInterval);
        expect(wasCancelled).toBe(true);
        expect(useTestStore.getState().activePolls).toEqual({});

        clearIntervalSpy.mockRestore();
    });

    test('retryTest calls clearInterval for each active poll and empties activePolls', () => {
        const fakeInterval = setInterval(() => {}, 10000);
        const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval');

        act(() => {
            useTestStore.setState({ activePolls: { 'ghost-task': fakeInterval } });
        });

        act(() => { useTestStore.getState().retryTest(); });

        const wasCancelled = clearIntervalSpy.mock.calls.some(args => args[0] === fakeInterval);
        expect(wasCancelled).toBe(true);
        expect(useTestStore.getState().activePolls).toEqual({});

        clearIntervalSpy.mockRestore();
    });
});
