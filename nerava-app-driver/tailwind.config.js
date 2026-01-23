/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'facebook-blue': '#1877F2',
        // Figma exact colors
        'text-primary': '#050505',
        'text-secondary': '#656A6B',
        'background-gray': '#F7F8FA',
        'border-gray': '#E4E6EB',
      },
      borderRadius: {
        'card': '16px', // Updated to match tokens.ts
        'button': '8px',
        'pill': '9999px',
        'modal': '20px',
      },
      boxShadow: {
        'card': '0 2px 8px rgba(0, 0, 0, 0.1)',
        'card-lg': '0 4px 16px rgba(0, 0, 0, 0.12)',
        'modal': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        // Figma exact drop shadows for featured card
        'figma-card': '0 2px 4px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.1)',
      },
      fontSize: {
        // Figma exact font sizes
        'figma-h1': ['30px', { lineHeight: '36px', letterSpacing: '0.395px', fontWeight: '500' }],
        'figma-h3': ['24px', { lineHeight: '32px', letterSpacing: '0.07px', fontWeight: '500' }],
        'figma-h4': ['16px', { lineHeight: '24px', letterSpacing: '-0.3125px', fontWeight: '500' }],
        'figma-body': ['14px', { lineHeight: '20px', letterSpacing: '-0.15px', fontWeight: '400' }],
        'figma-badge': ['12px', { lineHeight: '16px', letterSpacing: '0px', fontWeight: '500' }],
        'figma-small': ['12px', { lineHeight: '16px', letterSpacing: '0px', fontWeight: '400' }],
      },
    },
  },
  plugins: [],
}

