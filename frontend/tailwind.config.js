/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0f19",
        panel: "rgba(23, 30, 43, 0.7)",
        primary: "#8b5cf6",
        accent: "#3b82f6",
        muted: "#94a3b8",
      },
      backdropBlur: {
        glass: "16px",
      }
    },
  },
  plugins: [],
}
