/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"Source Sans 3"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      colors: {
        'canvas': '#FAFAF8',
        'charcoal': '#1A1A1A',
        'muted-surface': '#F5F3F0',
        'muted-text': '#6B6B6B',
        'gold': {
          DEFAULT: '#B8860B',
          secondary: '#D4A84B',
          muted: 'rgba(184, 134, 11, 0.08)',
          light: 'rgba(184, 134, 11, 0.08)',
        },
        'rule': {
          DEFAULT: '#E8E4DF',
          dark: '#D8D3CC',
        },
        'card': '#FFFFFF',
        'danger': '#dc3545',
        'warning': '#ffc107',
        'success': '#28a745',
        'info': '#17a2b8',
        'primary': '#007bff',
        'dark': '#1a1a1a',
        'light': '#f8f9fa',
      },
      boxShadow: {
        'subtle': '0 1px 2px rgba(26, 26, 26, 0.04)',
        'editorial': '0 4px 12px rgba(26, 26, 26, 0.06)',
        'elevated': '0 8px 24px rgba(26, 26, 26, 0.08)',
        'gold': '0 4px 14px rgba(184, 134, 11, 0.25)',
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
