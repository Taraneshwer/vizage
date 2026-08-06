
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4F97A3',
        secondary: '#F1F5F9',
        accent: '#14B8A6',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        background: '#FFFFFF',
        card: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
