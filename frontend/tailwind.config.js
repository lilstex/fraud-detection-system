/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Palette matched to the mockup diagrams used in the project report
        brand: {
          50:  '#EBF4FB',
          100: '#D9E7F5',
          500: '#3182CE',
          600: '#2C5282',
          700: '#1E3A5F',
        },
        risk: {
          high:   '#E53E3E',
          medium: '#DD6B20',
          low:    '#38A169',
        },
      },
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'serif'],
      },
    },
  },
  plugins: [],
}
