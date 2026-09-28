/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b0d11',
        surface: '#13171f',
        'surface-elevated': '#1a202c',
        primary: {
          DEFAULT: '#059669',
          light: '#10b981',
        }
      }
    },
  },
  plugins: [],
}
