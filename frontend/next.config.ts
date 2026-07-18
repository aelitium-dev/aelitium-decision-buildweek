import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

const backendBase = (process.env.AELITIUM_API_BASE_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export default function nextConfig(phase: string): NextConfig {
  return {
    // Next 15 otherwise lets `next dev` and `next build` overwrite the same
    // manifests. Keep their generated module graphs physically separate.
    distDir: phase === PHASE_DEVELOPMENT_SERVER ? ".next-dev" : ".next",
    async rewrites() {
      return [
        {
          source: "/api/backend/:path*",
          destination: `${backendBase}/:path*`,
        },
      ];
    },
  };
}
