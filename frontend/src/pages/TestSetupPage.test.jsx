import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import TestSetupPage from './TestSetupPage';
import useTestStore from '../store/testStore';
import { getQuestions } from '../services/api';

// Mock API includes 'question_counts' matching the real API shape
vi.mock('../services/api', () => ({
  getAvailableTests: vi.fn(() => Promise.resolve({
    data: [
      { category: 'History', scope: 'Ancient', version: '1.0', test_id: 'history_ancient', created_at: '2020-02-01T00:00:00Z', question_counts: { total: 2, closed: 2, open: 0 } },
      { category: 'History', scope: 'Poland', version: '1.0', test_id: 'history_poland', created_at: '2026-01-01T00:00:00Z', question_counts: { total: 10, closed: 8, open: 2 } },
      { category: 'Biology', scope: 'Cell', version: '1.2', test_id: 'biology_cell', created_at: '2023-06-01T00:00:00Z', question_counts: { total: 5, closed: 5, open: 0 } },
      { category: 'Art', scope: 'Cave', version: '1.0', test_id: 'art_cave', created_at: '2020-01-01T00:00:00Z', question_counts: { total: 20, closed: 20, open: 0 } },
    ]
  })),
  getQuestions: vi.fn(() => Promise.resolve({ data: [{id: 'q1', questionText: 'Test Question'}] })),
}));


describe('TestSetupPage - user interaction scenarios', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    act(() => {
      const { resetTest } = useTestStore.getState();
      resetTest();
      useTestStore.setState({ view: 'setup' });
    });
    vi.clearAllMocks();
  });

  test('should correctly render the page and load test categories', async () => {
    render(<TestSetupPage />);

    expect(screen.getByRole('heading', { name: /Select Category/i })).toBeInTheDocument();

    // `findByText` waits until mock API data is loaded.
    expect(await screen.findByText('History')).toBeInTheDocument();
    expect(await screen.findByText('Biology')).toBeInTheDocument();
  });

  test('should allow expanding a category and selecting specific tests', async () => {
    render(<TestSetupPage />);

    const historyCategoryButton = await screen.findByText('History');
    await user.click(historyCategoryButton);

    const historyCheckbox = await screen.findByLabelText(/Poland \(1.0\)/i);
    expect(historyCheckbox).toBeInTheDocument();

    expect(useTestStore.getState().selectedCategories).toEqual([]);

    await user.click(historyCheckbox);
    expect(useTestStore.getState().selectedCategories).toEqual(['history_poland']);

    await user.click(historyCheckbox);
    expect(useTestStore.getState().selectedCategories).toEqual([]);
  });

  test('"Start Test" button should be enabled after selecting a test and entering a question count', async () => {
    render(<TestSetupPage />);

    // Use async findByRole to wait for the button to change from "Loading..." to "Start Test".
    const startButton = await screen.findByRole('button', { name: /Start Test/i });
    expect(startButton).toBeDisabled();

    await user.click(screen.getByText('History'));
    await user.click(await screen.findByLabelText(/Poland \(1.0\)/i));

    await screen.findByText(/available: 8/);

    const numInput = screen.getByLabelText(/Number of questions/i);
    await user.clear(numInput);
    await user.type(numInput, '8');

    await waitFor(() => {
      expect(startButton).not.toBeDisabled();
    });
  });

  test('should start the test and trigger question fetching on button click', async () => {
    render(<TestSetupPage />);

    const startButton = await screen.findByRole('button', { name: /Start Test/i });

    await user.click(await screen.findByText('History'));
    await user.click(await screen.findByLabelText(/Poland \(1.0\)/i));

    await screen.findByText(/available: 8/);

    const numInput = screen.getByLabelText(/Number of questions/i);
    await user.clear(numInput);
    await user.type(numInput, '5');

    await waitFor(() => {
        expect(startButton).not.toBeDisabled();
    });

    await user.click(startButton);

    expect(useTestStore.getState().view).toBe('test');
    expect(getQuestions).toHaveBeenCalledOnce();
    expect(getQuestions).toHaveBeenCalledWith({
      categories: 'history_poland',
      num_questions: 5,
      mode: 'closed'
    });
  });

  test('filters the list by category or test name', async () => {
    render(<TestSetupPage />);
    await screen.findByText('History');

    await user.type(screen.getByLabelText(/search tests/i), 'cell');

    expect(screen.queryByText('History')).not.toBeInTheDocument();
    expect(screen.getByText('Biology')).toBeInTheDocument();
  });

  test('sorts categories alphabetically, by newest test, or by question count', async () => {
    render(<TestSetupPage />);
    await screen.findByText('History');

    const orderOf = () => ['Art', 'Biology', 'History']
      .map((name) => screen.getByRole('button', { name: new RegExp(`^${name}`) }))
      .sort((a, b) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1))
      .map((button) => button.textContent.match(/^(Art|Biology|History)/)[1]);

    expect(orderOf()).toEqual(['Art', 'Biology', 'History']);

    await user.click(screen.getByRole('button', { name: /^History/i }));
    const historyTestOrder = () => {
      const ancient = screen.getByLabelText(/Ancient \(1\.0\)/i);
      const poland = screen.getByLabelText(/Poland \(1\.0\)/i);
      return ancient.compareDocumentPosition(poland) & Node.DOCUMENT_POSITION_FOLLOWING
        ? ['Ancient', 'Poland']
        : ['Poland', 'Ancient'];
    };
    expect(historyTestOrder()).toEqual(['Ancient', 'Poland']);

    await user.selectOptions(screen.getByLabelText(/sort tests/i), 'newest');
    expect(historyTestOrder()).toEqual(['Poland', 'Ancient']);
    expect(orderOf()).toEqual(['History', 'Biology', 'Art']);

    await user.selectOptions(screen.getByLabelText(/sort tests/i), 'count');
    expect(orderOf()).toEqual(['Art', 'History', 'Biology']);
  });
});
