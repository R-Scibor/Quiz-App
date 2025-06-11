import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Rozszerza `expect` o dodatkowe, bardziej czytelne asercje, np. .toBeInTheDocument()
expect.extend(matchers);

// Uruchamia automatyczne czyszczenie (odmontowywanie komponentów) po każdym teście
afterEach(() => {
  cleanup();
});