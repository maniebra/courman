import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Django Ninja routes are registered with a trailing slash; without this,
  // Next's own trailing-slash redirect fires before the rewrite below runs.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      // `:path*` never captures the trailing slash, so without this first rule
      // `/api/courses/` proxies to `/api/courses` and Django's APPEND_SLASH
      // redirects it straight back — a 301 loop.
      { source: "/api/:path*/", destination: `${backendUrl}/api/:path*/` },
      { source: "/api/:path*", destination: `${backendUrl}/api/:path*` },
    ];
  },
};

export default nextConfig;
