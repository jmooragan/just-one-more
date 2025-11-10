# Just One More – Local Prototype

A lightweight React + Tailwind experience that helps families “pack one extra” meal. Everything is client-side and persists in `localStorage`, so it works offline-first with zero backend services.

---

## Stack
- Vite + React 18
- Tailwind CSS utilities
- `lucide-react` icon set

> Requires **Node.js 18+** and **npm** (or pnpm/yarn).

---

## Getting started

```bash
npm install
npm run dev
```

Vite prints the local URL (defaults to http://localhost:5173). The prototype seeds demo lighthouses on first load; reset everything via **Settings → Reset Data**.

### Additional scripts
- `npm run build` – create a production bundle in `dist/`
- `npm run preview` – serve the production bundle locally

---

## Features
- Contributor onboarding with optional contact + location capture, including automatic lighthouse suggestion via geolocation/Haversine distance.
- Meal logging with QR/container IDs, allergen flags, drop-off vs collection workflow, and quantity-based bulk codes.
- Keeper dashboard to receive/distribute meals, award loyalty points, and trigger milestone notifications.
- Impact view with badges, leaderboard, and notification timeline.
- WhatsApp CTA in the footer that opens a chat to +27 66 229 5868.

### Notes
- QR scanning is stubbed; integrate `html5-qrcode` or similar when needed.
- Notifications/geolocation require browser permission and a secure context (https or localhost).
- Clearing browser storage wipes the prototype data by design.
