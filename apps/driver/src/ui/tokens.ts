// Centralized design tokens matching Figma specifications exactly

export const colors = {
  // Primary
  facebookBlue: '#1877F2',
  facebookBlueHover: '#166FE5',
  
  // Figma exact colors (from RGB values)
  textPrimary: '#050505', // rgb(0.02, 0.02, 0.02)
  textSecondary: '#656A6B', // rgb(0.396, 0.404, 0.420)
  backgroundGray: '#F7F8FA', // rgb(0.969, 0.973, 0.980)
  borderGray: '#E4E6EB', // rgb(0.894, 0.902, 0.922)
  
  // Exclusive badge colors (from Figma)
  exclusiveYellowStart: '#F0B000', // rgb(0.941, 0.693, 0) with 15% opacity
  exclusiveYellowEnd: '#FE9A00', // rgb(0.994, 0.603, 0) with 15% opacity
  exclusiveBorder: '#D08700', // rgb(0.818, 0.530, 0) with 30% opacity
  
  // Neutral grays
  gray50: '#F9FAFB',
  gray100: '#F3F4F6',
  gray200: '#E5E7EB',
  gray300: '#D1D5DB',
  gray400: '#9CA3AF',
  gray500: '#6B7280',
  gray600: '#4B5563',
  gray700: '#374151',
  gray800: '#1F2937',
  gray900: '#111827',
  
  // Semantic colors
  success: '#10B981',
  successLight: '#D1FAE5',
  warning: '#F59E0B',
  warningLight: '#FEF3C7',
  error: '#EF4444',
  
  // Backgrounds
  white: '#FFFFFF',
  black: '#000000',
} as const

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '20px',
  '2xl': '24px',
  '3xl': '32px',
  '4xl': '40px',
  '5xl': '48px',
} as const

export const borderRadius = {
  button: '8px',
  card: '16px',
  modal: '20px',
  pill: '9999px',
} as const

export const shadows = {
  card: '0 2px 8px rgba(0, 0, 0, 0.1)',
  cardLg: '0 4px 16px rgba(0, 0, 0, 0.12)',
  modal: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  // Figma exact drop shadows for featured card
  figmaCard: '0 2px 4px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.1)',
} as const

export const typography = {
  fontFamily: {
    sans: [
      '-apple-system',
      'BlinkMacSystemFont',
      'Segoe UI',
      'Roboto',
      'Oxygen',
      'Ubuntu',
      'Cantarell',
      'Fira Sans',
      'Droid Sans',
      'Helvetica Neue',
      'sans-serif',
    ].join(', '),
  },
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px',
    '2xl': '24px',
    '3xl': '30px',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
  // Figma exact typography specifications
  figma: {
    heading1: {
      fontSize: '30px',
      fontWeight: 500,
      lineHeight: '36px',
      letterSpacing: '0.395px',
    },
    heading3: {
      fontSize: '24px',
      fontWeight: 500,
      lineHeight: '32px',
      letterSpacing: '0.07px',
    },
    heading4: {
      fontSize: '16px',
      fontWeight: 500,
      lineHeight: '24px',
      letterSpacing: '-0.3125px',
    },
    body: {
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: '20px',
      letterSpacing: '-0.15px',
    },
    badge: {
      fontSize: '12px',
      fontWeight: 500,
      lineHeight: '16px',
      letterSpacing: '0px',
    },
    small: {
      fontSize: '12px',
      fontWeight: 400,
      lineHeight: '16px',
      letterSpacing: '0px',
    },
  },
} as const

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
} as const

// Modal backdrop opacity
export const modalBackdropOpacity = 0.6

// Icon sizes
export const iconSizes = {
  sm: '16px',
  md: '24px',
  lg: '32px',
  xl: '48px',
} as const

// Export as default object for easy access
export default {
  colors,
  spacing,
  borderRadius,
  shadows,
  typography,
  breakpoints,
  modalBackdropOpacity,
  iconSizes,
}

