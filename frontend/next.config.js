/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
    API_KEY: process.env.API_KEY || ''
  }
}

module.exports = nextConfig