/**
 * Frontend configuration
 * Reads environment variables with fallbacks
 */

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL;

const normalizeApiUrl = (value?: string) => {
  if (!value) return 'https://zeusonic-api.onrender.com';

  const trimmed = value.trim().replace(/\/$/, '');
  const lower = trimmed.toLowerCase();

  if (lower.includes('localhost') || lower.includes('127.0.0.1')) {
    return 'https://zeusonic-api.onrender.com';
  }

  if (lower.startsWith('http://')) {
    return `https://${trimmed.slice('http://'.length)}`;
  }

  if (!lower.startsWith('https://')) {
    return 'https://zeusonic-api.onrender.com';
  }

  return trimmed;
};

export const config = {
  apiUrl: normalizeApiUrl(rawApiUrl),
} as const;
