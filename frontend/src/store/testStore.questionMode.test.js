import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';

describe('question mode preference', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.resetModules();
    });

    afterEach(() => {
        localStorage.clear();
    });

    test('starts from the saved open, closed, or mixed choice', async () => {
        localStorage.setItem('question_mode', 'mixed');
        const { default: useTestStore } = await import('./testStore');
        expect(useTestStore.getState().questionMode).toBe('mixed');
    });

    test('ignores a saved value that is not a question mode', async () => {
        localStorage.setItem('question_mode', 'essay');
        const { default: useTestStore } = await import('./testStore');
        expect(useTestStore.getState().questionMode).toBe('closed');
    });

    test('setQuestionMode writes the choice to localStorage', async () => {
        const { default: useTestStore } = await import('./testStore');
        useTestStore.getState().setQuestionMode('open');
        expect(localStorage.getItem('question_mode')).toBe('open');
        expect(useTestStore.getState().questionMode).toBe('open');
    });
});
