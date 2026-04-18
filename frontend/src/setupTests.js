import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extends `expect` with additional readable matchers, e.g. .toBeInTheDocument()
expect.extend(matchers);

// Runs automatic cleanup (unmounts components) after each test
afterEach(() => {
  cleanup();
});