import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import ReportModal from './ReportModal';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../services/api', () => ({
    reportIssue: vi.fn(),
}));

vi.mock('framer-motion', () => ({
    motion: new Proxy({}, {
        get: (_, tag) => {
            const Tag = typeof tag === 'string' ? tag : 'div';
            return ({ children, ...props }) => {
                // Strip framer-motion-specific props that cause React warnings
                const { variants: _variants, initial: _initial, animate: _animate, exit: _exit, transition: _transition, ...rest } = props;
                return React.createElement(Tag, rest, children);
            };
        },
    }),
    AnimatePresence: ({ children }) => <>{children}</>,
}));

vi.mock('./LoadingSpinner', () => ({
    default: ({ size }) => <span data-testid="spinner">{size}</span>,
}));

import { reportIssue as mockReportIssue } from '../services/api';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const OPEN_QUESTION = {
    id: 'q-open-1',
    type: 'open-text',
    questionText: 'Explain DNS.',
};

const CLOSED_QUESTION = {
    id: 'q-closed-1',
    type: 'single-choice',
    questionText: 'What color is the sky?',
};

const AI_FEEDBACK = { score: 2, feedback: 'Partial credit.', grading_method: 'llm' };

function renderModal(props = {}) {
    const defaults = {
        question: OPEN_QUESTION,
        testId: 'test-uuid-1',
        aiFeedback: null,
        userAnswer: 'My open text answer',
        onClose: vi.fn(),
        onReportSuccess: vi.fn(),
    };
    return render(<ReportModal {...defaults} {...props} />);
}

beforeEach(() => { vi.clearAllMocks(); });
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

describe('ReportModal — rendering', () => {
    test('renders with "Question error" radio selected by default', () => {
        renderModal();
        const radio = screen.getByRole('radio', { name: /błąd w pytaniu/i });
        expect(radio).toBeChecked();
    });

    test('shows AI grading option for open questions', () => {
        renderModal({ question: OPEN_QUESTION });
        expect(screen.getByRole('radio', { name: /niesłuszna ocena AI/i })).toBeInTheDocument();
    });

    test('hides AI grading option for closed questions', () => {
        renderModal({ question: CLOSED_QUESTION });
        expect(screen.queryByRole('radio', { name: /niesłuszna ocena AI/i })).toBeNull();
    });

    test('AI grading radio is disabled when aiFeedback is null', () => {
        renderModal({ question: OPEN_QUESTION, aiFeedback: null });
        expect(screen.getByRole('radio', { name: /niesłuszna ocena AI/i })).toBeDisabled();
    });

    test('AI grading radio is enabled when aiFeedback is present', () => {
        renderModal({ question: OPEN_QUESTION, aiFeedback: AI_FEEDBACK });
        expect(screen.getByRole('radio', { name: /niesłuszna ocena AI/i })).not.toBeDisabled();
    });
});

// ---------------------------------------------------------------------------
// Interactions
// ---------------------------------------------------------------------------

describe('ReportModal — interactions', () => {
    test('clicking Cancel calls onClose', async () => {
        const user = userEvent.setup();
        const onClose = vi.fn();
        renderModal({ onClose });

        await user.click(screen.getByRole('button', { name: /anuluj/i }));
        expect(onClose).toHaveBeenCalledOnce();
    });

    test('submit button is disabled while request is pending', async () => {
        const user = userEvent.setup();
        // Never-resolving promise to keep the pending state
        mockReportIssue.mockReturnValueOnce(new Promise(() => {}));
        renderModal({ question: OPEN_QUESTION, aiFeedback: null });

        // Get a reference to the submit button before clicking
        const submitBtn = screen.getByRole('button', { name: /wyślij/i });
        await user.click(submitBtn);

        // After clicking, the button renders the spinner — query by type=submit
        // because the button's accessible name changes to the spinner's text content.
        const disabledBtn = document.querySelector('button[type="submit"]');
        expect(disabledBtn).toBeDisabled();
    });
});

// ---------------------------------------------------------------------------
// Successful submission
// ---------------------------------------------------------------------------

describe('ReportModal — successful submission', () => {
    test('shows success message after submit', async () => {
        const user = userEvent.setup();
        mockReportIssue.mockResolvedValueOnce({ data: {} });
        renderModal();

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => {
            expect(screen.getByText(/dziękujemy/i)).toBeInTheDocument();
        });
    });

    test('calls onReportSuccess and onClose after the success timeout', async () => {
        // Intercept only the component's specific setTimeout(callback, 2000) call.
        // All other setTimeout calls (React internals, waitFor, userEvent) run normally
        // via the real implementation. This avoids fake-timer/userEvent interaction issues.
        const origSetTimeout = globalThis.setTimeout;
        let capturedCallback;
        vi.spyOn(globalThis, 'setTimeout').mockImplementation((fn, delay, ...args) => {
            if (delay === 2000) {
                capturedCallback = fn;
                return 0;
            }
            return origSetTimeout.call(globalThis, fn, delay, ...args);
        });

        const user = userEvent.setup();
        const onClose = vi.fn();
        const onReportSuccess = vi.fn();
        mockReportIssue.mockResolvedValueOnce({ data: {} });
        renderModal({ onClose, onReportSuccess });

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        // Wait until the component's try block has run and registered the timeout.
        await waitFor(() => expect(capturedCallback).toBeDefined());

        // Fire the captured callback directly (simulates the 2000ms elapsing).
        capturedCallback();

        expect(onReportSuccess).toHaveBeenCalledOnce();
        expect(onClose).toHaveBeenCalledOnce();
        // spy is restored in afterEach via vi.restoreAllMocks()
    });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

describe('ReportModal — error handling', () => {
    test('displays error message when API call fails', async () => {
        const user = userEvent.setup();
        mockReportIssue.mockRejectedValueOnce({ message: 'Server error 500' });
        renderModal();

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => {
            expect(screen.getByText(/server error 500/i)).toBeInTheDocument();
        });
    });

    test('falls back to generic message when error has no message', async () => {
        const user = userEvent.setup();
        mockReportIssue.mockRejectedValueOnce({});
        renderModal();

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => {
            expect(screen.getByText(/błąd podczas wysyłania/i)).toBeInTheDocument();
        });
    });
});

// ---------------------------------------------------------------------------
// Payload structure
// ---------------------------------------------------------------------------

describe('ReportModal — payload structure', () => {
    test('QUESTION_ERROR sends null ai_feedback_snapshot', async () => {
        const user = userEvent.setup();
        mockReportIssue.mockResolvedValueOnce({ data: {} });
        renderModal({ question: OPEN_QUESTION, aiFeedback: null });

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => expect(mockReportIssue).toHaveBeenCalled());
        const payload = mockReportIssue.mock.calls[0][0];
        expect(payload.ai_feedback_snapshot).toBeNull();
        expect(payload.issue_type).toBe('QUESTION_ERROR');
    });

    test('AI_GRADING_ERROR sends JSON.stringify(aiFeedback) as snapshot', async () => {
        const user = userEvent.setup();
        mockReportIssue.mockResolvedValueOnce({ data: {} });
        renderModal({ question: OPEN_QUESTION, aiFeedback: AI_FEEDBACK });

        // Select AI grading error
        await user.click(screen.getByRole('radio', { name: /niesłuszna ocena AI/i }));
        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => expect(mockReportIssue).toHaveBeenCalled());
        const payload = mockReportIssue.mock.calls[0][0];
        expect(payload.ai_feedback_snapshot).toBe(JSON.stringify(AI_FEEDBACK));
        expect(payload.issue_type).toBe('AI_GRADING_ERROR');
    });

    test('open question: user_answer_open set, user_answer_choices null', async () => {
        const user = userEvent.setup();
        mockReportIssue.mockResolvedValueOnce({ data: {} });
        renderModal({ question: OPEN_QUESTION, userAnswer: 'DNS does name resolution' });

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => expect(mockReportIssue).toHaveBeenCalled());
        const payload = mockReportIssue.mock.calls[0][0];
        expect(payload.user_answer_open).toBe('DNS does name resolution');
        expect(payload.user_answer_choices).toBeNull();
    });

    test('closed question: user_answer_choices set, user_answer_open null', async () => {
        const user = userEvent.setup();
        mockReportIssue.mockResolvedValueOnce({ data: {} });
        const choiceAnswer = [1]; // integer index
        renderModal({ question: CLOSED_QUESTION, userAnswer: choiceAnswer });

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => expect(mockReportIssue).toHaveBeenCalled());
        const payload = mockReportIssue.mock.calls[0][0];
        expect(payload.user_answer_choices).toEqual(choiceAnswer);
        expect(payload.user_answer_open).toBeNull();
    });

    test('closed question: pre-mapped text strings are sent as-is', async () => {
        // Callers (ReviewPage, TestScreenPage) map indices to option text before passing
        // userAnswer. The modal forwards the value unchanged.
        const user = userEvent.setup();
        mockReportIssue.mockResolvedValueOnce({ data: {} });
        const questionWithOptions = { ...CLOSED_QUESTION, options: ['Earth', 'Mars', 'Jupiter'] };
        renderModal({ question: questionWithOptions, userAnswer: ['Jupiter'] });

        await user.click(screen.getByRole('button', { name: /wyślij/i }));

        await waitFor(() => expect(mockReportIssue).toHaveBeenCalled());
        const payload = mockReportIssue.mock.calls[0][0];
        expect(payload.user_answer_choices).toEqual(['Jupiter']);
    });
});
