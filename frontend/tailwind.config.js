/** @type {import('tailwindcss').Config} */
const tokens = require('./design-tokens.json')

const colorTokens = tokens.color || {}
const fontTokens = tokens.font || {}
const spacingTokens = tokens.spacing || {}
const radiusTokens = tokens.radius || {}
const shadowTokens = tokens.shadow || {}

module.exports = {
  content: [
    './app/**/*.{ts,tsx,js,jsx}',
    './components/**/*.{ts,tsx,js,jsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        base: colorTokens.background,
        surface: colorTokens.surface,
        accent: colorTokens.accent,
        magenta: colorTokens.magenta,
        muted: colorTokens.muted,
        text: colorTokens.text,
      },
      fontFamily: {
        sans: [fontTokens.family.sans]
      },
      borderRadius: {
        DEFAULT: radiusTokens.DEFAULT,
        sm: radiusTokens.sm,
        pill: radiusTokens.pill
      },
      spacing: {
        '1': spacingTokens['1'],
        '2': spacingTokens['2'],
        '3': spacingTokens['3'],
        '4': spacingTokens['4'],
        '6': spacingTokens['6'],
        '8': spacingTokens['8'],
        '12': spacingTokens['12']
      },
      boxShadow: {
        soft: shadowTokens.soft,
        glow: shadowTokens.glow
      }
    },
  },
  plugins: [],
}
