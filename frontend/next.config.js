/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || '',
    NEXT_PUBLIC_API_KEY: process.env.NEXT_PUBLIC_API_KEY || process.env.API_KEY || ''
  }
}

module.exports = nextConfig
