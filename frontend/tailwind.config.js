/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: '#111827',
        'surface-light': '#1F2937',
        border: '#374151',
        primary: {
          50: '#EEF2FF',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA'
        },
        risk: {
          low: '#10B981',      // Emerald
          medium: '#F59E0B',   // Amber
          high: '#F97316',     // Orange
          critical: '#EF4444'  // Red/Crimson
        }
      }
    },
  },
  plugins: [],
}
