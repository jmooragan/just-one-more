# Just One More — Prototype

A lightweight React prototype for coordinating community meal contributions (“pack one extra”). Data is stored locally in the browser (no backend). Includes contributor onboarding, logging meals (with bulk IDs), lighthouse selection (auto-choose nearest), keeper workflow, impact/leaderboard, and WhatsApp contact.

---

## Tech stack
- **React** (Vite)
- **Tailwind CSS** for styling
- **lucide-react** for icons
- **LocalStorage** (in-browser “DB”)

> Requires **Node.js 18+** and **npm** (or **pnpm/yarn**).

---

## Quick start

### 1) Scaffold a Vite + React app
```bash
# choose a folder and run
npm create vite@latest jom -- --template react
cd jom

### 2) Install dependencies
npm i
npm i lucide-react
npm i -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

### 3) Configure Tailwind
Edit tailwind.config.js:
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: { extend: {} },
  plugins: [],
}

Replace src/index.css with:
@tailwind base;
@tailwind components;
@tailwind utilities;

### 4) Add the App code:
Replace src/App.jsx with the App.jsx from the repo
Ensure src/main.jsx renders <App />:
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)

Keep Vite’s default index.html (it already has <div id="root"></div>).

### 5) Run locally
npm run dev


Features

Contributor onboarding with optional contact and location capture

Nearest lighthouse auto-select (Haversine distance)

Log a meal with:

QR/container ID

Date and method (dropoff / collect)

Description

Meal type (Vegetarian/Beef/Pork/Fish)

Allergens checkboxes

Bulk save via Quantity dropdown (BASE-01, BASE-02, …)

Keeper view to receive and distribute meals (awards points + milestone notifications)

Impact: badges, leaderboard, and notifications

WhatsApp contact in footer (opens chat to +27 66 229 5868)

Notes & caveats

This prototype uses localStorage only; resetting data is available in Settings.

Camera QR scanning is stubbed; you can integrate e.g. html5-qrcode later.

Notifications require user permission and a supported browser (secure context). Geolocation prompts the user.

Repository structure (after setup)
jom/
├─ index.html
├─ package.json
├─ tailwind.config.js
├─ postcss.config.js
├─ .gitignore
├─ src/
│  ├─ App.jsx        # main app (paste your file here)
│  ├─ main.jsx
│  └─ index.css
└─ public/

