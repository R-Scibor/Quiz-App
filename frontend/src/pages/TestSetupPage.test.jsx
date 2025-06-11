import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import TestSetupPage from './TestSetupPage';
import useTestStore from '../store/testStore';

// Mockujemy cały moduł api.js. Oznacza to, że zamiast robić prawdziwe
// żądania sieciowe, testy będą używać naszych fałszywych danych.
vi.mock('../services/api', () => ({
  getAvailableTests: vi.fn(() => Promise.resolve({
    data: [
      { category: 'Historia', scope: 'Polska', version: '1.0', test_id: 'historia' },
      { category: 'Biologia', scope: 'Komórka', version: '1.2', test_id: 'biologia' },
    ]
  })),
  getQuestions: vi.fn(() => Promise.resolve({ data: [] })), // Na razie zwracamy pustą listę
}));


describe('TestSetupPage - interakcje użytkownika', () => {

  // Przed każdym testem resetujemy stan
  beforeEach(() => {
    act(() => {
      useTestStore.getState().resetTest();
    });
    // Czyścimy mocki, aby wywołania z poprzednich testów nie wpływały na kolejne
    vi.clearAllMocks();
  });

  test('powinien renderować stronę, pobierać i wyświetlać dostępne kategorie', async () => {
    render(<TestSetupPage />);

    // `findByText` poczeka, aż dane z "API" (naszego mocka) się załadują
    expect(await screen.findByText('Historia: Polska (v1.0)')).toBeInTheDocument();
    expect(screen.getByText('Biologia: Komórka (v1.2)')).toBeInTheDocument();
  });

  test('powinien pozwolić użytkownikowi wybrać i odznaczyć kategorie', async () => {
    const user = userEvent.setup();
    render(<TestSetupPage />);
    
    const historiaCheckbox = await screen.findByLabelText('Historia: Polska (v1.0)');
    const biologiaCheckbox = await screen.findByLabelText('Biologia: Komórka (v1.2)');

    // Początkowo nic nie jest zaznaczone w stanie
    expect(useTestStore.getState().selectedCategories).toEqual([]);

    // Użytkownik klika na historię
    await user.click(historiaCheckbox);
    expect(useTestStore.getState().selectedCategories).toEqual(['historia']);

    // Użytkownik klika na biologię
    await user.click(biologiaCheckbox);
    expect(useTestStore.getState().selectedCategories).toEqual(['historia', 'biologia']);

    // Użytkownik odznacza historię
    await user.click(historiaCheckbox);
    expect(useTestStore.getState().selectedCategories).toEqual(['biologia']);
  });

  test('przycisk "Rozpocznij Test" powinien być wyłączony, gdy żadna kategoria nie jest wybrana', async () => {
    render(<TestSetupPage />);
    
    // Czekamy na załadowanie kategorii
    await screen.findByText('Historia: Polska (v1.0)');
    
    const startButton = screen.getByRole('button', { name: /rozpocznij test/i });
    expect(startButton).toBeDisabled();
  });

  test('powinien zmienić widok na "test" po kliknięciu "Rozpocznij Test"', async () => {
    const user = userEvent.setup();
    render(<TestSetupPage />);

    const historiaCheckbox = await screen.findByLabelText('Historia: Polska (v1.0)');
    await user.click(historiaCheckbox);

    const startButton = screen.getByRole('button', { name: /rozpocznij test/i });
    expect(startButton).not.toBeDisabled();

    // Używamy `act`, ponieważ ta akcja spowoduje asynchroniczne zmiany stanu
    await act(async () => {
        await user.click(startButton);
    });

    // Sprawdzamy, czy stan w store został poprawnie zmieniony
    expect(useTestStore.getState().view).toBe('test');
  });

});
