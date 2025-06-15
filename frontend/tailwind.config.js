/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-background': '#1a1016',
        'brand-text': '#E6EDF3',
        'brand-primary': '#DC2525',
        'brand-primary-hover': '#ef4444',
        'brand-secondary': '#901E3E',
        'card-bg': 'rgba(22, 27, 34, 0.9)',
        'card-border': '#30363d',
        'option-bg': '#21262d',
      },
      boxShadow: {
        'primary': '0 4px 14px 0 rgba(220, 37, 37, 0.3)',
        'primary-hover': '0 6px 20px 0 rgba(220, 37, 37, 0.4)',
        'card': '0 8px 32px 0 rgba(0, 0, 0, 0.37), 0 0 75px rgba(144, 30, 62, 0.3)',
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
