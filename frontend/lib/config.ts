/**
 * Frontend configuration
 * Reads environment variables with fallbacks
 */

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'https://zeusonic-api.onrender.com',
} as const;
