import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import TestScreenPage from './TestScreenPage';
import useTestStore from '../store/testStore';

// Mock question data used across tests — gives full control over scenarios.
const mockQuestions = [
    { id: 'q1', questionText: 'What color is the sky?', type: 'single-choice', options: ['Green', 'Blue', 'Red'], correctAnswers: [1], explanation: 'The sky is typically blue during the day due to Rayleigh scattering.' },
    { id: 'q2', questionText: 'Which of the following are planets?', type: 'multiple-choice', options: ['Mars', 'Moon', 'Jupiter'], correctAnswers: [0, 2], explanation: 'The Moon is a natural satellite of Earth, not a planet.' },
];

describe('TestScreenPage - quiz solving scenarios', () => {
    const user = userEvent.setup();

    // Set state before each test as if the quiz has just started.
    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            useTestStore.setState({
                view: 'test',
                currentQuestions: mockQuestions,
                currentQuestionIndex: 0,
                userAnswers: {},
                score: 0,
            });
        });
    });

    test('should display the first question with answer options', () => {
        render(<TestScreenPage />);

        // Check that the question text is visible.
        expect(screen.getByText(mockQuestions[0].questionText)).toBeInTheDocument();
        // Answer options are divs, so find them by their text content.
        expect(screen.getByText('Green')).toBeInTheDocument();
        expect(screen.getByText('Blue')).toBeInTheDocument();
        expect(screen.getByText('Red')).toBeInTheDocument();
    });

    test('should allow selecting the correct answer, confirming it, and awarding a point', async () => {
        render(<TestScreenPage />);

        const correctAnswerOption = screen.getByText('Blue');
        const confirmButton = screen.getByRole('button', { name: /confirm/i });

        // User clicks the correct answer.
        await user.click(correctAnswerOption);

        // Check that the answer is saved in state (but not yet graded).
        expect(useTestStore.getState().userAnswers['q1']).toEqual([1]);

        // User clicks the "Confirm" button.
        await user.click(confirmButton);

        // Check that the point was awarded.
        expect(useTestStore.getState().score).toBe(1);
        // Check that the explanation appeared on screen.
        expect(screen.getByText(mockQuestions[0].explanation)).toBeInTheDocument();
    });

    test('should advance to the next question after clicking the "Next" button', async () => {
        render(<TestScreenPage />);

        // Simulate answering the first question.
        await user.click(screen.getByText('Blue'));
        await user.click(screen.getByRole('button', { name: /confirm/i }));

        // After confirming, the "Next" button appears.
        const nextButton = screen.getByRole('button', { name: /next/i });
        await user.click(nextButton);

        // Check that the question index in state was updated.
        expect(useTestStore.getState().currentQuestionIndex).toBe(1);
        // Check that the second question text is now on screen.
        expect(screen.getByText(mockQuestions[1].questionText)).toBeInTheDocument();
    });

    test('should finish the test and show "View results" button after the last question', async () => {
        // Set state so the test is on the last question.
        act(() => {
            useTestStore.setState({ currentQuestionIndex: 1 });
        });
        render(<TestScreenPage />);

        // User answers the last question.
        await user.click(screen.getByText('Mars'));
        await user.click(screen.getByRole('button', { name: /confirm/i }));

        // On the last question the navigation button text changes.
        const finishButton = screen.getByRole('button', { name: /view results/i });
        await user.click(finishButton);

        // Check that the view state changed to 'results', indicating end of test.
        expect(useTestStore.getState().view).toBe('results');
    });

    // -------------------------------------------------------------------------
    // Scoring edge cases
    // -------------------------------------------------------------------------

    test('confirmAnswer scores correctly when all multiple-choice options selected', async () => {
        // Use the second question (multiple-choice: correctAnswers=[0, 2] for Mars+Jupiter)
        act(() => {
            useTestStore.setState({ currentQuestionIndex: 1, score: 0 });
        });
        render(<TestScreenPage />);

        // Select both correct answers
        await user.click(screen.getByText('Mars'));
        await user.click(screen.getByText('Jupiter'));
        await user.click(screen.getByRole('button', { name: /confirm/i }));

        expect(useTestStore.getState().score).toBe(1);
    });

    test('confirmAnswer accepts correct answers regardless of selection order', async () => {
        // Select in reverse order: Jupiter then Mars (correct is [0, 2] → Mars, Jupiter)
        act(() => {
            useTestStore.setState({ currentQuestionIndex: 1, score: 0 });
        });
        render(<TestScreenPage />);

        await user.click(screen.getByText('Jupiter'));
        await user.click(screen.getByText('Mars'));
        await user.click(screen.getByRole('button', { name: /confirm/i }));

        expect(useTestStore.getState().score).toBe(1);
    });

    test('confirmAnswer does not score when only partial selection made', async () => {
        // Only select Mars (index 0) but not Jupiter (index 2) → incorrect
        act(() => {
            useTestStore.setState({ currentQuestionIndex: 1, score: 0 });
        });
        render(<TestScreenPage />);

        await user.click(screen.getByText('Mars')); // only one of two required
        await user.click(screen.getByRole('button', { name: /confirm/i }));

        expect(useTestStore.getState().score).toBe(0);
    });

    test('nextQuestion on last question transitions to results view', async () => {
        // Patch _finalizeSession to prevent real API calls
        const mockFinalize = vi.fn().mockResolvedValue(undefined);
        act(() => {
            useTestStore.setState({
                currentQuestionIndex: 1,
                _finalizeSession: mockFinalize,
            });
        });
        render(<TestScreenPage />);

        await user.click(screen.getByText('Mars'));
        await user.click(screen.getByRole('button', { name: /confirm/i }));
        await user.click(screen.getByRole('button', { name: /view results/i }));

        expect(useTestStore.getState().view).toBe('results');
    });
});
