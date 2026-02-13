import type { NextConfig } from "next";

const proxyTarget =
  process.env.API_PROXY_TARGET ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    const normalizedTarget = proxyTarget.replace(/\/$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${normalizedTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
