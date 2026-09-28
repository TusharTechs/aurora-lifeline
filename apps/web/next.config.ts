import path from "node:path";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// The repo keeps one git-ignored .env at its root; load it for the web build too.
// forceReload: Next has already loaded (and cached) env for apps/web before reading this file.
loadEnvConfig(
  path.resolve(__dirname, "../.."),
  process.env.NODE_ENV !== "production",
  { info: () => {}, error: console.error },
  true,
);

// Static export only: no SSR, no framework-aware Firebase deploy (CLAUDE.md, Stack).
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
};

export default nextConfig;
