# JustOneMore — Reverse Uber Eats Charity App (Streamlit MVP)

A Streamlit-based MVP for a charity food collection pipeline: cooks prepare extra meals, drivers collect and drop at hubs, hubs dispatch to lighthouses, and lighthouses distribute to beneficiaries — with QR tracking and map-assisted routing.

Key features:
- Roles: Cook, Driver, Hub, Lighthouse
- QR-based chain-of-custody for dishes
- Allergen tagging and food safety guide
- Map of pickups and Google Maps navigation deep links
- Contributor profile with points and badges
- SQLite persistence with simple seed data


## Quickstart

Requirements: Python 3.9+ (3.10+ recommended).

1) Install dependencies:

   pip install -r requirements.txt

2) Run the app:

   streamlit run app.py

3) First-run setup:
- Open the app in your browser (Streamlit shows the URL).
- Go to Admin and click “Seed default hub and lighthouse”.
- Go to “Sign up / Sign in” to create your profile and choose roles.

## Project files
- App entrypoint: [app.py](app.py)
- Dependencies: [requirements.txt](requirements.txt)
- Data directory (auto-created): data/
  - SQLite DB: data/app.db
  - Generated QR images: data/qrcodes/


## End-to-end flow

1) Cook logs a pickup
- Enter dish name, description, portions, allergens, dates.
- Set pickup address and optionally geocode to lat/lon.
- App generates a QR code image; print and stick on the container.
- Dish starts in status: prepared.

2) Driver collects and drops at hub
- Add DRIVER role on your profile if needed.
- Start a trip. Enter current location (or use saved coordinates).
- See available pickups sorted by proximity and shown on a map.
- Navigate via Google Maps deep links.
- At pickup, scan the dish QR (or enter code manually) to mark picked_up.
- Navigate to the nearest hub; at hub intake, scan QR to mark at_hub.

3) Hub assigns to Lighthouse
- Hub operator scans incoming dishes to mark at_hub.
- Select one or more dishes and assign them to a lighthouse. Status moves to assigned_to_lighthouse.

4) Lighthouse receives and distributes
- On arrival, scan dish to mark at_lighthouse.
- When distributing to beneficiaries, scan again to mark distributed.
- The original cook is notified in-app that their dish was distributed.


## Map integration

- The pickups map uses Streamlit’s built-in st.map to show points.
- Google Maps navigation is provided via deep links; example:

   https://www.google.com/maps/dir/?api=1&origin=-33.925,18.424&destination=-33.930,18.420

- Origin is optional; when omitted, the link uses only destination.
- Enhancements to consider:
  - Use pydeck for richer maps with clustering and routing overlays.
  - Use streamlit-folium (Leaflet) for polygon zones and better popups.
  - Add OSRM/GraphHopper routing or distance matrix for optimized routes.
  - Add live driver location sharing and auto-reordering of pickups.


## QR codes

- Payload format: JOM1|<dish_uuid>
- Generated when a cook creates a dish; saved under data/qrcodes/{dish_id}.png
- Scanning:
  - Primary: Streamlit camera (st.camera_input) decodes via OpenCV if available.
  - Fallback: Remote decoding service (api.qrserver.com).
  - Manual: Enter the payload string if camera decoding fails.
- If running offline or without a camera, use manual entry.


## Allergen tagging

Built-in list (editable in code): Gluten, Crustaceans, Eggs, Fish, Peanuts, Soybeans, Milk, Nuts, Celery, Mustard, Sesame, Sulphites, Lupin, Molluscs. These are recorded per dish and shown to drivers/hubs/lighthouses.


## Data model and statuses

Entities:
- users: id, name, email, phone, roles (JSON), address, lat, lon
- dishes: id, cook_id, title, description, allergens, portions, prepared_at, expiry_date, status, pickup_(address|lat|lon), qr_payload, qr_path, trip_id, hub_id, lighthouse_id
- trips: id, driver_id, started_at, ended_at, status
- hubs: id, name, address, lat, lon
- lighthouses: id, name, address, lat, lon
- notifications: id, user_id, dish_id, type, message, created_at, read

Status lifecycle:
prepared → picked_up → at_hub → assigned_to_lighthouse → at_lighthouse → distributed


## Geocoding

- Address-to-coordinates uses OpenStreetMap Nominatim.
- Respect rate limits; avoid batch geocoding from the UI.
- Update the USER_AGENT constant in [app.py](app.py) with your contact email or domain.
- You can manually enter lat/lon if geocoding fails.


## Food Safety Guide

A concise guide is available under “Safety Guide” in the sidebar, including hygiene checklist and allergen labelling best practices. Customize the copy in [app.py](app.py).


## Profiles, points, and badges

The profile page shows counts for dishes cooked, pickups driven, and dishes distributed, plus a simple points total and sample badges (First Cook, Home Chef 10, First Pickup, Road Hero 20, Impact Maker).


## Seeding and resetting data

- Seed defaults via Admin → “Seed default hub and lighthouse”.
- Reset DB by stopping the app and deleting data/app.db and data/qrcodes/.


## Known limitations

- No password auth; sign-in is by email only (demo).
- Single-tenant SQLite; no multi-user syncing or concurrent locks considered.
- Camera access may be blocked by browser permissions; manual QR entry provided.
- Remote QR decode requires internet access.
- Geocoding is subject to third-party rate limits and availability.
- Not a medical/food authority; follow local regulations for food safety.


## Roadmap ideas and map-focused suggestions

- Driver route optimization across multiple pickups (Greedy TSP + constraints).
- Capacity-aware assignment (vehicle capacity vs. portions).
- Real-time driver tracking; auto-assign nearest hub; live ETA.
- Heatmaps of demand/supply; hub coverage polygons; lighthouse catchments.
- SMS/WhatsApp notifications (Twilio/WhatsApp API) for cooks and drivers.
- Export CSVs; audit logs; admin reports and dashboards.
- Replace deep links with embedded map widgets and turn-by-turn instruction panes.


## Troubleshooting

- On Windows, if camera is not detected, try Chrome/Edge and ensure site permissions allow camera; or use manual code entry.
- If Google Maps links don’t open, copy the link and paste into a new tab; ensure "&" characters are not HTML-escaped.
- If geocoding fails, try a simpler address or add city/country; otherwise input lat/lon directly.


## License and use

This MVP is provided for charitable use and demonstration purposes. No warranties; use at your own risk.


## Credits

Built with Streamlit, SQLite, OpenStreetMap Nominatim, and qrcode. See [requirements.txt](requirements.txt).


## Optional Canva materials

For outreach/training, consider creating Canva assets (poster, step-by-step handout, QR label template). This codebase focuses on the functioning MVP; Canva assets can complement onboarding and safety communication.