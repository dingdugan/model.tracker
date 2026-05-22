import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // monochrome + one accent
        ink:    { DEFAULT: "#0a0a0a", soft: "#1a1a1a", muted: "#525252", line: "#262626" },
        paper:  { DEFAULT: "#fafaf9", panel: "#f5f5f4", line: "#e7e5e4" },
        accent: { DEFAULT: "#dc2626", soft: "#fee2e2" },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "PingFang SC", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
