import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // next 15+ uses turbopack.root for workspace root
    // @ts-ignore
    turbopack: {
      root: '.',
      resolveAlias: {
        './typst.css?inline': './src/app/typst/styles/typst.css',
      },
    },
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      './typst.css?inline': './src/app/typst/styles/typst.css',
    };
    return config;
  },
};

export default nextConfig;
