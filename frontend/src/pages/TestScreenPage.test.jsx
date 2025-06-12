import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';

import TestScreenPage from './TestScreenPage';
import useTestStore from '../store/testStore';

// Mockujemy przykładowe dane pytań, które będą używane w testach.
// Dzięki temu mamy pełną kontrolę nad danymi i scenariuszami.
const mockQuestions = [
    { id: 'q1', questionText: 'Jakiego koloru jest niebo?', type: 'single-choice', options: ['Zielonego', 'Niebieskiego', 'Czerwonego'], correctAnswers: [1], explanation: 'Niebo w dzień jest zazwyczaj niebieskie z powodu rozpraszania Rayleigha.' },
    { id: 'q2', questionText: 'Które z poniższych są planetami?', type: 'multiple-choice', options: ['Mars', 'Księżyc', 'Jowisz'], correctAnswers: [0, 2], explanation: 'Księżyc jest naturalnym satelitą Ziemi, a nie planetą.' },
];

describe('TestScreenPage - Scenariusze rozwiązywania testu', () => {
    const user = userEvent.setup();

    // Przed każdym testem ustawiamy stan tak, jakby test właśnie się rozpoczął.
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

    test('powinien wyświetlić pierwsze pytanie wraz z opcjami odpowiedzi', () => {
        render(<TestScreenPage />);
        
        // Sprawdzamy, czy tekst pytania jest widoczny.
        expect(screen.getByText(mockQuestions[0].questionText)).toBeInTheDocument();
        // Opcje odpowiedzi to divy, więc szukamy ich po tekście, który zawierają.
        expect(screen.getByText('Zielonego')).toBeInTheDocument();
        expect(screen.getByText('Niebieskiego')).toBeInTheDocument();
        expect(screen.getByText('Czerwonego')).toBeInTheDocument();
    });

    test('powinien pozwolić na zaznaczenie poprawnej odpowiedzi, zatwierdzenie jej i zaliczenie punktu', async () => {
        render(<TestScreenPage />);
        
        const correctAnswerOption = screen.getByText('Niebieskiego');
        const confirmButton = screen.getByRole('button', { name: /zatwierdź/i });

        // Użytkownik klika na poprawną odpowiedź.
        await user.click(correctAnswerOption);
        
        // Sprawdzamy, czy odpowiedź została zapisana w stanie (ale jeszcze nie oceniona).
        expect(useTestStore.getState().userAnswers['q1']).toEqual([1]);

        // Użytkownik klika przycisk "Zatwierdź".
        await user.click(confirmButton);
        
        // Sprawdzamy, czy punkt został przyznany.
        expect(useTestStore.getState().score).toBe(1);
        // Sprawdzamy, czy na ekranie pojawiło się wyjaśnienie.
        expect(screen.getByText(mockQuestions[0].explanation)).toBeInTheDocument();
    });

    test('powinien przejść do następnego pytania po kliknięciu przycisku "Dalej"', async () => {
        render(<TestScreenPage />);

        // Symulujemy cykl odpowiedzi na pierwsze pytanie.
        await user.click(screen.getByText('Niebieskiego'));
        await user.click(screen.getByRole('button', { name: /zatwierdź/i }));

        // Po zatwierdzeniu pojawia się przycisk "Dalej".
        const nextButton = screen.getByRole('button', { name: /dalej/i });
        await user.click(nextButton);

        // Sprawdzamy, czy indeks pytania w stanie został zaktualizowany.
        expect(useTestStore.getState().currentQuestionIndex).toBe(1);
        // Sprawdzamy, czy na ekranie jest już treść drugiego pytania.
        expect(screen.getByText(mockQuestions[1].questionText)).toBeInTheDocument();
    });

    test('powinien zakończyć test i pokazać przycisk "Zobacz wyniki" po ostatnim pytaniu', async () => {
        // Ustawiamy stan tak, aby test był na ostatnim pytaniu.
        act(() => {
            useTestStore.setState({ currentQuestionIndex: 1 });
        });
        render(<TestScreenPage />);

        // Użytkownik odpowiada na ostatnie pytanie.
        await user.click(screen.getByText('Mars'));
        await user.click(screen.getByRole('button', { name: /zatwierdź/i }));
        
        // Na ostatnim pytaniu przycisk do nawigacji zmienia tekst.
        const finishButton = screen.getByRole('button', { name: /zobacz wyniki/i });
        await user.click(finishButton);
        
        // Sprawdzamy, czy widok w stanie zmienił się na 'results', co oznacza koniec testu.
        expect(useTestStore.getState().view).toBe('results');
    });
});
