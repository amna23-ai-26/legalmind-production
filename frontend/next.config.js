/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://legalmind-production-production.up.railway.app/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
