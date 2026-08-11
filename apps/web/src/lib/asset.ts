// Prefix static assets with the deploy base path (GitHub Pages serves the site
// under /<repo>/). NEXT_PUBLIC_BASE_PATH is empty for local dev and Vercel.
const BASE = process.env.NEXT_PUBLIC_BASE_PATH || "";

export function asset(path: string): string {
  return `${BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export const basePath = BASE;
