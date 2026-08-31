import { describe, test, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import useTestStore from './testStore';

vi.mock('../services/api', () => ({
    getAvailableTests: vi.fn(),
    getQuestions: vi.fn(),
    checkOpenAnswer: vi.fn(),
    getTaskResult: vi.fn(),
    reportIssue: vi.fn(),
    startSession: vi.fn(),
    completeSession: vi.fn(),
    submitAttempts: vi.fn(),
    getUserStats: vi.fn(),
    getStudyQueue: vi.fn(),
    getStudyStats: vi.fn(),
    getTestStats: vi.fn(),
    registerUser: vi.fn(),
    loginUser: vi.fn(),
    logoutUser: vi.fn(),
}));

import { loginUser as mockLoginUser, registerUser as mockRegisterUser, logoutUser as mockLogoutUser } from '../services/api';

function resetAuthState() {
    act(() => {
        useTestStore.setState({
            user: null,
            authToken: null,
            isAuthLoading: false,
            authError: null,
            view: 'home',
        });
    });
    localStorage.clear();
    vi.clearAllMocks();
}

// ---------------------------------------------------------------------------
// initAuth
// ---------------------------------------------------------------------------

describe('useTestStore - initAuth', () => {
    beforeEach(resetAuthState);

    test('restores token and username from localStorage', () => {
        localStorage.setItem('auth_token', 'tok123');
        localStorage.setItem('auth_username', 'alice');

        act(() => { useTestStore.getState().initAuth(); });

        const state = useTestStore.getState();
        expect(state.authToken).toBe('tok123');
        expect(state.user?.username).toBe('alice');
    });

    test('is a no-op when localStorage is empty', () => {
        act(() => { useTestStore.getState().initAuth(); });

        const state = useTestStore.getState();
        expect(state.authToken).toBeNull();
        expect(state.user).toBeNull();
    });

    test('is a no-op when only auth_token is present (username missing)', () => {
        localStorage.setItem('auth_token', 'tok123');
        // auth_username deliberately omitted

        act(() => { useTestStore.getState().initAuth(); });

        expect(useTestStore.getState().user).toBeNull();
    });

    test('is a no-op when only auth_username is present (token missing)', () => {
        localStorage.setItem('auth_username', 'bob');

        act(() => { useTestStore.getState().initAuth(); });

        expect(useTestStore.getState().authToken).toBeNull();
    });
});

// ---------------------------------------------------------------------------
// login
// ---------------------------------------------------------------------------

describe('useTestStore - login', () => {
    beforeEach(resetAuthState);

    test('success: sets authToken, user.username, view=home', async () => {
        mockLoginUser.mockResolvedValueOnce({ data: { token: 'tok-abc', username: 'carol' } });

        await act(async () => {
            await useTestStore.getState().login({ username: 'carol', password: 'pass' });
        });

        const state = useTestStore.getState();
        expect(state.authToken).toBe('tok-abc');
        expect(state.user?.username).toBe('carol');
        expect(state.view).toBe('home');
        expect(state.isAuthLoading).toBe(false);
    });

    test('success: persists token and username to localStorage', async () => {
        mockLoginUser.mockResolvedValueOnce({ data: { token: 'tok-persist', username: 'dave' } });

        await act(async () => {
            await useTestStore.getState().login({ username: 'dave', password: 'pass' });
        });

        expect(localStorage.getItem('auth_token')).toBe('tok-persist');
        expect(localStorage.getItem('auth_username')).toBe('dave');
    });

    test('failure: sets authError, leaves user=null, isAuthLoading=false', async () => {
        const err = { message: 'Invalid credentials', code: 'INVALID_CREDENTIALS' };
        mockLoginUser.mockRejectedValueOnce(err);

        await act(async () => {
            await useTestStore.getState().login({ username: 'eve', password: 'wrong' });
        });

        const state = useTestStore.getState();
        expect(state.user).toBeNull();
        expect(state.authToken).toBeNull();
        expect(state.authError).toEqual(err);
        expect(state.isAuthLoading).toBe(false);
    });

    test('sets isAuthLoading=true during pending request', async () => {
        let resolveLogin;
        mockLoginUser.mockReturnValueOnce(
            new Promise(resolve => { resolveLogin = resolve; })
        );

        act(() => {
            // Don't await — let it hang
            useTestStore.getState().login({ username: 'frank', password: 'pass' });
        });

        expect(useTestStore.getState().isAuthLoading).toBe(true);

        // Clean up
        await act(async () => {
            resolveLogin({ data: { token: 'tok', username: 'frank' } });
        });
    });
});

// ---------------------------------------------------------------------------
// register
// ---------------------------------------------------------------------------

describe('useTestStore - register', () => {
    beforeEach(resetAuthState);

    test('success: sets authToken, user.username, view=home', async () => {
        mockRegisterUser.mockResolvedValueOnce({ data: { token: 'reg-tok', username: 'grace' } });

        await act(async () => {
            await useTestStore.getState().register({ username: 'grace', password: 'newpass' });
        });

        const state = useTestStore.getState();
        expect(state.authToken).toBe('reg-tok');
        expect(state.user?.username).toBe('grace');
        expect(state.view).toBe('home');
    });

    test('success: persists to localStorage', async () => {
        mockRegisterUser.mockResolvedValueOnce({ data: { token: 'reg-tok2', username: 'henry' } });

        await act(async () => {
            await useTestStore.getState().register({ username: 'henry', password: 'pass' });
        });

        expect(localStorage.getItem('auth_token')).toBe('reg-tok2');
        expect(localStorage.getItem('auth_username')).toBe('henry');
    });

    test('failure: sets authError', async () => {
        const err = { message: 'Username taken', code: 'DUPLICATE' };
        mockRegisterUser.mockRejectedValueOnce(err);

        await act(async () => {
            await useTestStore.getState().register({ username: 'existing', password: 'pass' });
        });

        expect(useTestStore.getState().authError).toEqual(err);
        expect(useTestStore.getState().user).toBeNull();
    });
});

// ---------------------------------------------------------------------------
// logout
// ---------------------------------------------------------------------------

describe('useTestStore - logout', () => {
    beforeEach(() => {
        resetAuthState();
        // Set up a logged-in state
        act(() => {
            useTestStore.setState({
                authToken: 'tok-logout',
                user: { username: 'ivan' },
            });
        });
        localStorage.setItem('auth_token', 'tok-logout');
        localStorage.setItem('auth_username', 'ivan');
    });

    test('clears authToken and user', async () => {
        mockLogoutUser.mockResolvedValueOnce({});

        await act(async () => { await useTestStore.getState().logout(); });

        const state = useTestStore.getState();
        expect(state.authToken).toBeNull();
        expect(state.user).toBeNull();
    });

    test('removes both localStorage keys', async () => {
        mockLogoutUser.mockResolvedValueOnce({});

        await act(async () => { await useTestStore.getState().logout(); });

        expect(localStorage.getItem('auth_token')).toBeNull();
        expect(localStorage.getItem('auth_username')).toBeNull();
    });

    test('clears local state even when API call throws', async () => {
        mockLogoutUser.mockRejectedValueOnce(new Error('Network error'));

        await act(async () => { await useTestStore.getState().logout(); });

        // Local state must be cleared despite the API failure
        expect(useTestStore.getState().authToken).toBeNull();
        expect(useTestStore.getState().user).toBeNull();
        expect(localStorage.getItem('auth_token')).toBeNull();
    });
});

describe('useTestStore - handleUnauthorized', () => {
    beforeEach(() => {
        resetAuthState();
        act(() => {
            useTestStore.setState({
                authToken: 'expired-tok',
                user: { username: 'ivan' },
                view: 'stats',
                currentSessionId: 'session-1',
            });
        });
        localStorage.setItem('auth_token', 'expired-tok');
        localStorage.setItem('auth_username', 'ivan');
    });

    test('clears auth and sends the user to login with a session-expired message', () => {
        act(() => { useTestStore.getState().handleUnauthorized(); });

        const state = useTestStore.getState();
        expect(state.authToken).toBeNull();
        expect(state.user).toBeNull();
        expect(state.view).toBe('login');
        expect(state.authError?.code).toBe('SESSION_EXPIRED');
        expect(state.authError?.message).toMatch(/session expired/i);
        expect(localStorage.getItem('auth_token')).toBeNull();
        expect(localStorage.getItem('auth_username')).toBeNull();
        expect(mockLogoutUser).not.toHaveBeenCalled();
    });

    test('mid-quiz: leaves the test view and says progress was not saved', () => {
        act(() => {
            useTestStore.setState({ view: 'test', currentSessionId: 'session-1' });
        });

        act(() => { useTestStore.getState().handleUnauthorized(); });

        const state = useTestStore.getState();
        expect(state.view).toBe('login');
        expect(state.currentSessionId).toBeNull();
        expect(state.authError?.message).toMatch(/not saved/i);
    });
});

// ---------------------------------------------------------------------------
// goToLogin / goToRegister
// ---------------------------------------------------------------------------

describe('useTestStore - navigation helpers', () => {
    beforeEach(resetAuthState);

    test('goToLogin: sets view=login and clears authError', () => {
        act(() => {
            useTestStore.setState({ authError: { message: 'old error' }, view: 'home' });
        });

        act(() => { useTestStore.getState().goToLogin(); });

        const state = useTestStore.getState();
        expect(state.view).toBe('login');
        expect(state.authError).toBeNull();
    });

    test('goToRegister: sets view=register and clears authError', () => {
        act(() => {
            useTestStore.setState({ authError: { message: 'old error' }, view: 'home' });
        });

        act(() => { useTestStore.getState().goToRegister(); });

        const state = useTestStore.getState();
        expect(state.view).toBe('register');
        expect(state.authError).toBeNull();
    });
});
