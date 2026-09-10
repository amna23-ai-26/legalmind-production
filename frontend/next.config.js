/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://YOUR-RAILWAY-BACKEND-URL.up.railway.app/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
