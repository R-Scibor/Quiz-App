import { describe, test, expect, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import useTestStore from './testStore';

// `describe` grupuje powiązane ze sobą testy
describe('useTestStore - testowanie logiki stanu', () => {

  // Hook `beforeEach` jest uruchamiany przed każdym testem w tej grupie.
  // Tutaj resetujemy stan do początkowych wartości, aby testy były od siebie niezależne.
  beforeEach(() => {
    act(() => {
      useTestStore.getState().resetTest();
    });
  });

  test('powinien mieć poprawny stan początkowy', () => {
    const initialState = useTestStore.getState();
    expect(initialState.view).toBe('home'); 
    expect(initialState.availableTests).toEqual([]);
    expect(initialState.selectedCategories).toEqual([]);
    expect(initialState.score).toBe(0);
    expect(initialState.isLoading).toBe(false);
  });

  test('akcja toggleCategory powinna poprawnie dodawać i usuwać kategorię', () => {
    // Sprawdzamy dodanie pierwszej kategorii
    act(() => {
      useTestStore.getState().toggleCategory('historia');
    });
    expect(useTestStore.getState().selectedCategories).toEqual(['historia']);

    // Sprawdzamy dodanie drugiej kategorii
    act(() => {
      useTestStore.getState().toggleCategory('biologia');
    });
    expect(useTestStore.getState().selectedCategories).toEqual(['historia', 'biologia']);

    // Sprawdzamy usunięcie pierwszej kategorii
    act(() => {
      useTestStore.getState().toggleCategory('historia');
    });
    expect(useTestStore.getState().selectedCategories).toEqual(['biologia']);
  });

  test('akcja setConfig powinna poprawnie ustawiać konfigurację', () => {
    act(() => {
      useTestStore.getState().setConfig(25, true);
    });
    const state = useTestStore.getState();
    expect(state.numQuestionsConfig).toBe(25);
    expect(state.timerEnabled).toBe(true);
  });

  test('akcja resetTest powinna przywracać stan do wartości domyślnych', () => {
    // Najpierw "brudzimy" stan
    act(() => {
      useTestStore.getState().toggleCategory('historia');
      useTestStore.getState().setConfig(50, true);
      useTestStore.setState({ score: 5, view: 'results' });
    });

    let dirtyState = useTestStore.getState();
    expect(dirtyState.selectedCategories).toEqual(['historia']);
    expect(dirtyState.score).toBe(5);
    expect(dirtyState.view).toBe('results');

    // Teraz resetujemy i sprawdzamy
    act(() => {
      useTestStore.getState().resetTest();
    });

    let cleanState = useTestStore.getState();
    expect(cleanState.selectedCategories).toEqual([]);
    expect(cleanState.score).toBe(0);
    expect(cleanState.view).toBe('home');
  });

});
