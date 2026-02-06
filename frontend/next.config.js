/** @type {import('next').NextConfig} */
// Build timestamp: 2026-02-07 cache-bust
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  webpack: (config) => {
    config.module.rules.push({
      test: /\.stories\.(ts|tsx|js|jsx)$/,
      use: 'null-loader',
    })
    return config
  },
}

module.exports = nextConfig
