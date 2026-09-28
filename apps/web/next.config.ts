import type { NextConfig } from "next";

// Static export only: no SSR, no framework-aware Firebase deploy (CLAUDE.md, Stack).
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
};

export default nextConfig;
