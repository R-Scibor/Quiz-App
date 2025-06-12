import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import TestSetupPage from './TestSetupPage';
import useTestStore from '../store/testStore';
// Kluczowa zmiana: Importujemy `getQuestions`, aby móc śledzić jego wywołania.
import { getQuestions } from '../services/api';

// Mockujemy moduł API, aby testy nie wykonywały prawdziwych zapytań sieciowych.
vi.mock('../services/api', () => ({
  getAvailableTests: vi.fn(() => Promise.resolve({
    data: [
      { category: 'Historia', scope: 'Polska', version: '1.0', test_id: 'historia_polska' },
      { category: 'Biologia', scope: 'Komórka', version: '1.2', test_id: 'biologia_komorka' },
    ]
  })),
  // Ważne: `getQuestions` jest teraz śledzoną funkcją mockującą (vi.fn).
  getQuestions: vi.fn(() => Promise.resolve({ data: [{id: 'q1', questionText: 'Test Question'}] })),
}));


describe('TestSetupPage - Scenariusze interakcji użytkownika', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    act(() => {
      useTestStore.getState().resetTest();
    });
    // Czyścimy historię wywołań mocków przed każdym testem.
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

  test('przycisk "Rozpocznij Test" powinien być nieaktywny, dopóki nie zostanie wybrany żaden test', async () => {
    render(<TestSetupPage />);

    await screen.findByText('Historia');
    const startButton = screen.getByRole('button', { name: /Rozpocznij Test/i });

    expect(startButton).toBeDisabled();

    await user.click(screen.getByText('Historia'));
    await user.click(await screen.findByLabelText(/Polska \(1.0\)/i));
    
    expect(startButton).not.toBeDisabled();
  });

  test('powinien rozpoczynać test i wywoływać pobieranie pytań po kliknięciu przycisku', async () => {
    render(<TestSetupPage />);

    await user.click(await screen.findByText('Historia'));
    await user.click(await screen.findByLabelText(/Polska \(1.0\)/i));

    const startButton = screen.getByRole('button', { name: /Rozpocznij Test/i });

    // Używamy `act` do opakowania interakcji, która powoduje asynchroniczną zmianę stanu
    await act(async () => {
      await user.click(startButton);
    });

    // Sprawdzamy, czy widok w store został poprawnie zmieniony.
    expect(useTestStore.getState().view).toBe('test');
    
    // POPRAWKA: Sprawdzamy, czy zamockowana funkcja `getQuestions` z modułu API została wywołana.
    expect(getQuestions).toHaveBeenCalled();
    // Możemy też sprawdzić, z jakimi argumentami została wywołana.
    expect(getQuestions).toHaveBeenCalledWith({
        categories: 'historia_polska',
        num_questions: 10 // Domyślna wartość ze stanu
    });
  });
});
