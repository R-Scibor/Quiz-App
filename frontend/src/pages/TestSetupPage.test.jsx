import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import TestSetupPage from './TestSetupPage';
import useTestStore from '../store/testStore';
import { getQuestions } from '../services/api';

// POPRAWKA: Mock API teraz zawiera 'question_counts', tak jak prawdziwe API
vi.mock('../services/api', () => ({
  getAvailableTests: vi.fn(() => Promise.resolve({
    data: [
      { category: 'Historia', scope: 'Polska', version: '1.0', test_id: 'historia_polska', question_counts: { total: 10, closed: 8, open: 2 } },
      { category: 'Biologia', scope: 'Komórka', version: '1.2', test_id: 'biologia_komorka', question_counts: { total: 5, closed: 5, open: 0 } },
    ]
  })),
  getQuestions: vi.fn(() => Promise.resolve({ data: [{id: 'q1', questionText: 'Test Question'}] })),
}));


describe('TestSetupPage - Scenariusze interakcji użytkownika', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    act(() => {
      const { resetTest } = useTestStore.getState();
      resetTest();
      useTestStore.setState({ view: 'setup' });
    });
    vi.clearAllMocks();
  });

  test('powinien poprawnie renderować stronę i wczytywać kategorie testów', async () => {
    render(<TestSetupPage />);

    expect(screen.getByRole('heading', { name: /Wybierz Kategorię/i })).toBeInTheDocument();
    
    // `findByText` poczeka, aż dane z mocka API zostaną załadowane.
    expect(await screen.findByText('Historia')).toBeInTheDocument();
    expect(await screen.findByText('Biologia')).toBeInTheDocument();
  });

  test('powinien pozwalać na rozwijanie kategorii i wybieranie konkretnych testów', async () => {
    render(<TestSetupPage />);

    const historiaCategoryButton = await screen.findByText('Historia');
    await user.click(historiaCategoryButton);
    
    const historiaCheckbox = await screen.findByLabelText(/Polska \(1.0\)/i);
    expect(historiaCheckbox).toBeInTheDocument();

    expect(useTestStore.getState().selectedCategories).toEqual([]);

    await user.click(historiaCheckbox);
    expect(useTestStore.getState().selectedCategories).toEqual(['historia_polska']);

    await user.click(historiaCheckbox);
    expect(useTestStore.getState().selectedCategories).toEqual([]);
  });

  test('przycisk "Rozpocznij Test" powinien być aktywny po wybraniu testu i wpisaniu liczby pytań', async () => {
    render(<TestSetupPage />);
    
    // POPRAWKA: Używamy asynchronicznego findByRole, aby poczekać, aż przycisk
    // zmieni tekst z "Ładowanie..." na "Rozpocznij Test".
    const startButton = await screen.findByRole('button', { name: /Rozpocznij Test/i });
    expect(startButton).toBeDisabled();

    await user.click(screen.getByText('Historia'));
    await user.click(await screen.findByLabelText(/Polska \(1.0\)/i));
    
    await screen.findByText(/dostępnych: 8/);

    const numInput = screen.getByLabelText(/Liczba pytań/i);
    await user.clear(numInput);
    await user.type(numInput, '8');
    
    await waitFor(() => {
      expect(startButton).not.toBeDisabled();
    });
  });

  test('powinien rozpoczynać test i wywoływać pobieranie pytań po kliknięciu przycisku', async () => {
    render(<TestSetupPage />);
    
    // POPRAWKA: Tutaj również czekamy na załadowanie komponentu.
    const startButton = await screen.findByRole('button', { name: /Rozpocznij Test/i });

    await user.click(await screen.findByText('Historia'));
    await user.click(await screen.findByLabelText(/Polska \(1.0\)/i));
    
    await screen.findByText(/dostępnych: 8/);

    const numInput = screen.getByLabelText(/Liczba pytań/i);
    await user.clear(numInput);
    await user.type(numInput, '5');
    
    await waitFor(() => {
        expect(startButton).not.toBeDisabled();
    });

    await user.click(startButton);

    expect(useTestStore.getState().view).toBe('test');
    expect(getQuestions).toHaveBeenCalledOnce();
    expect(getQuestions).toHaveBeenCalledWith({
      categories: 'historia_polska',
      num_questions: 5,
      mode: 'closed'
    });
  });
});