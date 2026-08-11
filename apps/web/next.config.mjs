// Two build modes:
//   default        - dev/server build; /api is proxied to the FastAPI backend
//   STATIC_EXPORT  - fully static export for GitHub Pages (landing + client app shell).
//                    Rewrites can't run in an export, so the app talks to the backend
//                    via NEXT_PUBLIC_API_BASE_URL instead.
const isExport = process.env.STATIC_EXPORT === "1";
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  ...(isExport
    ? {
        output: "export",
        basePath: basePath || undefined,
        images: { unoptimized: true },
        trailingSlash: true,
      }
    : {
        async rewrites() {
          const api = process.env.API_PROXY_TARGET || "http://localhost:8000";
          return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
        },
      }),
};

export default nextConfig;
