import type { NextConfig } from "next";

// Where this app's server reaches the backend (the API gateway, or the SkyForge server when hosted)
const gateway = (process.env.API_GATEWAY_URL ?? "http://localhost:8080").replace(/\/$/, "");

const nextConfig: NextConfig = {
  // The browser calls the API on this app's own origin and the server forwards it. A hosted frontend is
  // HTTPS (camera and microphone only work on secure pages), and browsers block an HTTPS page's calls to
  // the plain-HTTP backend; same-origin calls also need no CORS.
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${gateway}/api/v1/:path*` }];
  },
  experimental: {
    // Forwarded requests time out after 30 s by default; a Skillaro lesson from the local LLM can take longer
    proxyTimeout: 300_000,
  },
};

export default nextConfig;
