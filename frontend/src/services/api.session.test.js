import { describe, test, expect } from 'vitest';
import { shouldTreatAsExpiredSession } from './api';

describe('shouldTreatAsExpiredSession', () => {
    test('true for 401 on an authenticated endpoint when a token is present', () => {
        expect(shouldTreatAsExpiredSession({
            status: 401,
            url: '/stats/',
            hasToken: true,
        })).toBe(true);
    });

    test('false for 401 on login (bad credentials, not an expired session)', () => {
        expect(shouldTreatAsExpiredSession({
            status: 401,
            url: '/auth/login/',
            hasToken: true,
        })).toBe(false);
    });

    test('false for 401 on register', () => {
        expect(shouldTreatAsExpiredSession({
            status: 401,
            url: '/auth/register/',
            hasToken: true,
        })).toBe(false);
    });

    test('false for 401 on logout (avoids a handler loop)', () => {
        expect(shouldTreatAsExpiredSession({
            status: 401,
            url: '/auth/logout/',
            hasToken: true,
        })).toBe(false);
    });

    test('false when no token is stored (anonymous 401)', () => {
        expect(shouldTreatAsExpiredSession({
            status: 401,
            url: '/stats/',
            hasToken: false,
        })).toBe(false);
    });

    test('false for non-401 errors', () => {
        expect(shouldTreatAsExpiredSession({
            status: 500,
            url: '/stats/',
            hasToken: true,
        })).toBe(false);
    });

    test('matches relative urls that include the auth path as a suffix', () => {
        expect(shouldTreatAsExpiredSession({
            status: 401,
            url: '/api/v1/auth/login/',
            hasToken: true,
        })).toBe(false);
        expect(shouldTreatAsExpiredSession({
            status: 401,
            url: '/api/v1/sessions/start/',
            hasToken: true,
        })).toBe(true);
    });
});
