/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  eslint: {
    // Don't fail the build on ESLint errors during production builds
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;

