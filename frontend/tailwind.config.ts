import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
    "./3d-scenes/**/*.{js,ts,jsx,tsx}",
    "./store/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--color-bg)",
        surface: "var(--color-surface)",
        primary: "var(--color-primary)",
        accent: "var(--color-accent)"
      },
      boxShadow: {
        glow: "var(--shadow-glow)"
      }
    }
  },
  plugins: []
};

export default config;
