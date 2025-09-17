/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL || 'http://localhost:8000',
    NEXT_PUBLIC_API_KEY: process.env.NEXT_PUBLIC_API_KEY || process.env.API_KEY || ''
  }
}

module.exports = nextConfig
