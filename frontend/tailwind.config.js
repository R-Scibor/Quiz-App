/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Ta linia mówi Tailwind, żeby skanował wszystkie pliki w folderze src
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}