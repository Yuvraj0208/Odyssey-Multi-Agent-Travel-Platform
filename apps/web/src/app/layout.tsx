import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });
const display = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Odyssey - AI travel, planned by a team of agents",
  description:
    "Describe a trip and watch a team of seven specialized AI agents research, plan, and price it in real time - grounded in live weather, real places, and real walking times.",
  openGraph: {
    title: "Odyssey - AI travel, planned by a team of agents",
    description:
      "Seven specialized AI agents plan your trip live, grounded in real open tourism data. Watch them work.",
    type: "website",
  },
};

// Apply the persisted theme before paint to avoid a flash.
const themeScript = `(function(){try{var t=localStorage.getItem('odyssey-theme')||'dark';document.documentElement.classList.toggle('dark',t!=='light');}catch(e){document.documentElement.classList.add('dark');}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${mono.variable} ${display.variable} dark`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-bg text-fg antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
