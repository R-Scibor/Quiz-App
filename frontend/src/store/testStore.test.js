import { describe, test, expect, beforeEach } from 'vitest';
import { act } from '@testing-library/react';
import useTestStore from './testStore';

// `describe` groups related tests
describe('useTestStore - state logic tests', () => {

  // `beforeEach` runs before each test in this group.
  // Reset state to initial values so tests are independent.
  beforeEach(() => {
    act(() => {
      useTestStore.getState().resetTest();
    });
  });

  test('should have the correct initial state', () => {
    const initialState = useTestStore.getState();
    expect(initialState.view).toBe('home');
    expect(initialState.availableTests).toEqual([]);
    expect(initialState.selectedCategories).toEqual([]);
    expect(initialState.score).toBe(0);
    expect(initialState.isLoading).toBe(false);
  });

  test('toggleCategory action should correctly add and remove a category', () => {
    // Check adding the first category
    act(() => {
      useTestStore.getState().toggleCategory('history');
    });
    expect(useTestStore.getState().selectedCategories).toEqual(['history']);

    // Check adding the second category
    act(() => {
      useTestStore.getState().toggleCategory('biology');
    });
    expect(useTestStore.getState().selectedCategories).toEqual(['history', 'biology']);

    // Check removing the first category
    act(() => {
      useTestStore.getState().toggleCategory('history');
    });
    expect(useTestStore.getState().selectedCategories).toEqual(['biology']);
  });

  test('setConfig action should correctly set the configuration', () => {
    act(() => {
      useTestStore.getState().setConfig(25, true);
    });
    const state = useTestStore.getState();
    expect(state.numQuestionsConfig).toBe(25);
    expect(state.timerEnabled).toBe(true);
  });

  test('resetTest action should restore state to default values', () => {
    // First "dirty" the state
    act(() => {
      useTestStore.getState().toggleCategory('history');
      useTestStore.getState().setConfig(50, true);
      useTestStore.setState({ score: 5, view: 'results' });
    });

    let dirtyState = useTestStore.getState();
    expect(dirtyState.selectedCategories).toEqual(['history']);
    expect(dirtyState.score).toBe(5);
    expect(dirtyState.view).toBe('results');

    // Now reset and verify
    act(() => {
      useTestStore.getState().resetTest();
    });

    let cleanState = useTestStore.getState();
    expect(cleanState.selectedCategories).toEqual([]);
    expect(cleanState.score).toBe(0);
    expect(cleanState.view).toBe('home');
  });

});
