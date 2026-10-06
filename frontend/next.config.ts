import type { NextConfig } from "next";

// Static export per brief §8: no SSR, no server actions, no image optimisation.
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
