import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import TestScreenPage from './TestScreenPage';
import useTestStore from '../store/testStore';

// Przykładowe dane pytań do testów
const mockQuestions = [
    { id: 1, questionText: 'Pytanie 1 (jednokrotny wybór)', type: 'single-choice', options: ['A', 'B', 'C'], correctAnswers: [1], explanation: 'Wyjaśnienie 1' },
    { id: 2, questionText: 'Pytanie 2 (wielokrotny wybór)', type: 'multiple-choice', options: ['X', 'Y', 'Z'], correctAnswers: [0, 2], explanation: 'Wyjaśnienie 2' },
];

describe('TestScreenPage - odpowiadanie na pytania', () => {

    // Przed każdym testem resetujemy stan i ustawiamy go tak, jakby test się właśnie rozpoczął
    beforeEach(() => {
        act(() => {
            useTestStore.getState().resetTest();
            // Symulujemy stan po rozpoczęciu testu
            useTestStore.setState({ 
                view: 'test', 
                currentQuestions: mockQuestions,
                currentQuestionIndex: 0,
            });
        });
    });

    test('powinien wyświetlić pierwsze pytanie i opcje odpowiedzi', () => {
        render(<TestScreenPage />);
        expect(screen.getByText('Pytanie 1 (jednokrotny wybór)')).toBeInTheDocument();
        expect(screen.getByLabelText('A')).toBeInTheDocument();
        expect(screen.getByLabelText('B')).toBeInTheDocument();
        expect(screen.getByLabelText('C')).toBeInTheDocument();
    });

    test('powinien pozwolić na zaznaczenie odpowiedzi i jej zatwierdzenie', async () => {
        const user = userEvent.setup();
        render(<TestScreenPage />);
        
        const optionB = screen.getByLabelText('B'); // Poprawna odpowiedź
        const confirmButton = screen.getByRole('button', { name: /zatwierdź/i });

        // Użytkownik wybiera opcję B
        await user.click(optionB);
        expect(useTestStore.getState().userAnswers[1]).toEqual([1]);

        // Użytkownik klika "Zatwierdź"
        await user.click(confirmButton);
        
        // Sprawdzamy, czy wynik się zwiększył
        expect(useTestStore.getState().score).toBe(1);
        
        // Sprawdzamy, czy pojawiło się wyjaśnienie
        expect(screen.getByText('Wyjaśnienie 1')).toBeInTheDocument();
    });

    test('powinien przejść do następnego pytania po kliknięciu "Następne pytanie"', async () => {
        const user = userEvent.setup();
        render(<TestScreenPage />);

        // Symulujemy odpowiedź na pierwsze pytanie
        await user.click(screen.getByLabelText('A')); // Nieważne co, byleby aktywować przycisk
        await user.click(screen.getByRole('button', { name: /zatwierdź/i }));

        // Pojawia się przycisk "Następne pytanie"
        const nextButton = screen.getByRole('button', { name: /następne pytanie/i });
        await user.click(nextButton);

        // Sprawdzamy, czy stan się zaktualizował
        expect(useTestStore.getState().currentQuestionIndex).toBe(1);

        // Sprawdzamy, czy na ekranie jest treść drugiego pytania
        expect(screen.getByText('Pytanie 2 (wielokrotny wybór)')).toBeInTheDocument();
    });

    test('powinien zakończyć test po ostatnim pytaniu', async () => {
        const user = userEvent.setup();
        // Ustawiamy test na ostatnie pytanie
        act(() => {
            useTestStore.setState({ currentQuestionIndex: 1 });
        });
        render(<TestScreenPage />);

        // Odpowiadamy na ostatnie pytanie
        await user.click(screen.getByLabelText('X'));
        await user.click(screen.getByRole('button', { name: /zatwierdź/i }));

        // Klikamy "Następne pytanie"
        const nextButton = screen.getByRole('button', { name: /następne pytanie/i });
        await user.click(nextButton);
        
        // Sprawdzamy, czy widok zmienił się na 'results'
        expect(useTestStore.getState().view).toBe('results');
    });
});
