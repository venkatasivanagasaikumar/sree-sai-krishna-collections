/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ssk: {
          navy: '#123F7A',
          'navy-dark': '#082B55',
          'blue-royal': '#1769AA',
          'blue-light': '#EAF3FC',
          gold: '#C89A43',
          'gold-light': '#E5B963',
          'gold-dark': '#A37728',
          text: '#1D2939',
          'text-secondary': '#667085',
          border: '#E4EAF2',
          surface: '#F7F9FC',
          success: '#15803D',
          warning: '#B7791F',
          error: '#DC2626'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
