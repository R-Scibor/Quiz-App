import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    // Umożliwia używanie globalnych funkcji Vitest (describe, test, expect) bez importowania ich w każdym pliku
    globals: true,
    // Ustawia środowisko testowe na 'jsdom' (symuluje przeglądarkę)
    environment: 'jsdom',
    // Wskazuje plik, który ma być uruchomiony przed testami (do konfiguracji)
    setupFiles: './src/setupTests.js',
  },
})
