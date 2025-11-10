/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          primary: "#7A4E2B",
          sand: "#F7EFE7",
        },
      },
    },
  },
  plugins: [],
};
