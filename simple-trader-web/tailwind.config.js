/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f0f0f',
        foreground: '#fafafa',
        card: {
          DEFAULT: '#1a1a1a',
          foreground: '#fafafa',
        },
        primary: {
          DEFAULT: '#22c55e',
          foreground: '#000000',
        },
        secondary: {
          DEFAULT: '#262626',
          foreground: '#fafafa',
        },
        muted: {
          DEFAULT: '#262626',
          foreground: '#a3a3a3',
        },
        accent: {
          DEFAULT: '#262626',
          foreground: '#fafafa',
        },
        destructive: {
          DEFAULT: '#ef4444',
          foreground: '#000000',
        },
        success: '#22c55e',
        warning: '#f59e0b',
        error: '#ef4444',
        profit: '#22c55e',
        loss: '#ef4444',
        border: '#333333',
        input: '#262626',
        ring: '#22c55e',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
