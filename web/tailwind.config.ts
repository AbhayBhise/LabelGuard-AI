/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1B4FD8",
        danger: "#DC2626",
        success: "#16A34A",
        warning: "#D97706",
        surface: "#FFFFFF",
        base: "#F8FAFC",
        textbase: "#0F172A",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace"],
      },
    },
  },
  plugins: [],
};
