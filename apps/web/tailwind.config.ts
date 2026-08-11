import type { Config } from "tailwindcss";

/**
 * Odyssey design tokens. Semantic colors resolve to CSS variables (see
 * globals.css) so light/dark are a single source of truth. Restrained neutral
 * palette + one accent (aurora indigo), per the design language.
 */
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--bg) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-2": "rgb(var(--surface-2) / <alpha-value>)",
        elevated: "rgb(var(--elevated) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",
        "border-strong": "rgb(var(--border-strong) / <alpha-value>)",
        fg: "rgb(var(--fg) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        faint: "rgb(var(--faint) / <alpha-value>)",
        accent: "rgb(var(--accent) / <alpha-value>)",
        "accent-fg": "rgb(var(--accent-fg) / <alpha-value>)",
        "accent-soft": "rgb(var(--accent-soft) / <alpha-value>)",
        success: "rgb(var(--success) / <alpha-value>)",
        warning: "rgb(var(--warning) / <alpha-value>)",
        danger: "rgb(var(--danger) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      borderRadius: {
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgb(0 0 0 / 0.04), 0 4px 16px rgb(0 0 0 / 0.06)",
        lift: "0 2px 4px rgb(0 0 0 / 0.06), 0 12px 32px rgb(0 0 0 / 0.10)",
        glow: "0 0 0 1px rgb(var(--accent) / 0.25), 0 8px 30px rgb(var(--accent) / 0.20)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgb(var(--accent) / 0.5)" },
          "70%": { boxShadow: "0 0 0 8px rgb(var(--accent) / 0)" },
          "100%": { boxShadow: "0 0 0 0 rgb(var(--accent) / 0)" },
        },
        // Landing: slow cinematic drift on hero photography
        kenburns: {
          "0%": { transform: "scale(1.06) translate3d(0, 0, 0)" },
          "100%": { transform: "scale(1.18) translate3d(-1.5%, -1.5%, 0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        aurora: {
          "0%, 100%": { transform: "translate(-8%, -4%) scale(1)" },
          "33%": { transform: "translate(6%, 4%) scale(1.12)" },
          "66%": { transform: "translate(-4%, 8%) scale(0.95)" },
        },
        "scroll-hint": {
          "0%": { transform: "translateY(0)", opacity: "0" },
          "35%": { opacity: "1" },
          "100%": { transform: "translateY(12px)", opacity: "0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.35s cubic-bezier(0.22, 1, 0.36, 1)",
        shimmer: "shimmer 2s linear infinite",
        "pulse-ring": "pulse-ring 1.8s cubic-bezier(0.22, 1, 0.36, 1) infinite",
        kenburns: "kenburns 26s ease-in-out infinite alternate",
        float: "float 6s ease-in-out infinite",
        aurora: "aurora 22s ease-in-out infinite",
        "scroll-hint": "scroll-hint 2s ease-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
