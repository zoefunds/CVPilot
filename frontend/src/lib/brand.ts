// Single source of truth for brand tokens.
// Keep in sync with the CSS variables in globals.css.

export const brand = {
  bg: '#efece4',
  bgSoft: '#f6f4ee',
  ink: '#1a1814',
  inkSoft: '#3a342c',
  accent: '#2b4f3a',
  accentSoft: '#cfd9d0',
  warn: '#a35f1f',
  danger: '#9b2226',
  line: '#d9d5c8',
} as const;

export const appName = process.env.NEXT_PUBLIC_APP_NAME || 'CVPilot';
export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
