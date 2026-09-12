/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'danger': '#dc3545',
        'warning': '#ffc107',
        'success': '#28a745',
        'info': '#17a2b8',
        'primary': '#007bff',
        'dark': '#1a1a1a',
        'light': '#f8f9fa',
      },
      animation: {
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        slide: 'slide 0.3s ease-in-out',
      },
      keyframes: {
        slide: {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
