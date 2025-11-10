# JustOneMore - Professional Food Donation Platform (Streamlit MVP)

import os
import io
import json
import math
import sqlite3
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import streamlit as st
import pandas as pd
import requests
from PIL import Image
import qrcode
import pydeck as pdk
import streamlit.components.v1 as components

# Optional OpenCV for local QR decoding
try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False

APP_NAME = "JustOneMore"
APP_TAGLINE = "Turning surplus into support, one meal at a time"
DATA_DIR = Path("data")
QRCODE_DIR = DATA_DIR / "qrcodes"
DB_PATH = DATA_DIR / "app.db"
USER_AGENT = "JustOneMore/1.0 (contact: example@example.com)"

ALLERGENS = [
    "Gluten", "Crustaceans", "Eggs", "Fish", "Peanuts", "Soybeans",
    "Milk", "Nuts", "Celery", "Mustard", "Sesame", "Sulphites", "Lupin", "Molluscs"
]

STATUSES = ["prepared", "picked_up", "at_hub", "assigned_to_lighthouse", "at_lighthouse", "distributed"]

# Ensure folders
DATA_DIR.mkdir(parents=True, exist_ok=True)
QRCODE_DIR.mkdir(parents=True, exist_ok=True)

# Settings storage
SETTINGS_PATH = DATA_DIR / "settings.json"
DEFAULT_SETTINGS = {"user_agent": USER_AGENT, "qr_fallback_enabled": True}

def load_settings() -> Dict[str, Any]:
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_SETTINGS.copy()
        merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(cfg: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def get_setting(key: str, default: Any = None) -> Any:
    try:
        cfg = load_settings()
        return cfg.get(key, default)
    except Exception:
        return default

# ---------------------------
# Styling
# ---------------------------
def inject_custom_css():
    st.markdown("""
        <style>
        /* Main container improvements */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }
        
        /* Modern button styling */
        .stButton > button {
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid #e0e0e0;
            background: white;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: #4CAF50;
        }
        
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            border: none;
        }
        
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
        }
        
        /* Card-like containers */
        .element-container {
            background: white;
            border-radius: 10px;
        }
        
        /* Header styling */
        h1 {
            color: #2c3e50;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        h2, h3 {
            color: #34495e;
            font-weight: 600;
            margin-top: 1.5rem;
        }
        
        /* Info boxes */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        /* Metric styling */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #4CAF50;
        }
        
        /* Form improvements */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            border-radius: 6px;
            border: 1px solid #ddd;
            padding: 0.6rem;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.1);
        }
        
        /* Navigation pills */
        .nav-pill {
            display: inline-block;
            padding: 0.5rem 1rem;
            margin: 0.25rem;
            border-radius: 20px;
            background: #f5f5f5;
            color: #333;
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .nav-pill:hover {
            background: #4CAF50;
            color: white;
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-prepared { background: #fff3cd; color: #856404; }
        .status-picked_up { background: #d1ecf1; color: #0c5460; }
        .status-at_hub { background: #d4edda; color: #155724; }
        .status-distributed { background: #c3e6cb; color: #155724; }
        
        /* Expander improvements */
        .streamlit-expanderHeader {
            background: #f8f9fa;
            border-radius: 6px;
            font-weight: 500;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Custom badge styling */
        .badge-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 500;
            font-size: 0.9rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------
# Utility helpers
# ---------------------------
def uuid() -> str:
    import uuid as _uuid
    return str(_uuid.uuid4())

def now_ts() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            roles TEXT NOT NULL,
            address TEXT,
            lat REAL,
            lon REAL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hubs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT,
            lat REAL,
            lon REAL
        );

        CREATE TABLE IF NOT EXISTS lighthouses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT,
            lat REAL,
            lon REAL
        );

        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            driver_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY(driver_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS dishes (
            id TEXT PRIMARY KEY,
            cook_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            allergens TEXT,
            portions INTEGER NOT NULL,
            prepared_at TEXT NOT NULL,
            expiry_date TEXT,
            status TEXT NOT NULL,
            pickup_address TEXT,
            pickup_lat REAL,
            pickup_lon REAL,
            qr_payload TEXT,
            qr_path TEXT,
            trip_id TEXT,
            hub_id TEXT,
            lighthouse_id TEXT,
            FOREIGN KEY(cook_id) REFERENCES users(id),
            FOREIGN KEY(trip_id) REFERENCES trips(id),
            FOREIGN KEY(hub_id) REFERENCES hubs(id),
            FOREIGN KEY(lighthouse_id) REFERENCES lighthouses(id)
        );

        CREATE INDEX IF NOT EXISTS idx_dishes_status ON dishes(status);
        CREATE INDEX IF NOT EXISTS idx_dishes_cook ON dishes(cook_id);

        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            dish_id TEXT,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            read INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(dish_id) REFERENCES dishes(id)
        );
    """)
    conn.commit()
    conn.close()

@st.cache_data(show_spinner=False)
def geocode_address(addr: str) -> Optional[Tuple[float, float]]:
    if not addr:
        return None
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": addr, "format": "json", "limit": 1}
        headers = {"User-Agent": str(get_setting("user_agent", USER_AGENT))}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        r.raise_for_status()
        items = r.json()
        if items:
            return float(items[0]["lat"]), float(items[0]["lon"])
    except Exception:
        return None
    return None

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def google_maps_dir_link(origin: Optional[Tuple[float,float]], dest: Tuple[float,float]) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={dest[0]},{dest[1]}&travelmode=driving"

def gmaps_multi_stop_link(origin: Tuple[float, float], waypoints: List[Tuple[float, float]], dest: Tuple[float, float]) -> str:
    wp = "|".join([f"{lat},{lon}" for (lat, lon) in waypoints])
    base = f"https://www.google.com/maps/dir/?api=1&destination={dest[0]},{dest[1]}&travelmode=driving"
    if wp:
        base += f"&waypoints={wp}"
    return base

def _read_geo_from_query() -> Optional[Tuple[float, float]]:
    try:
        params = st.query_params
        lat = params.get("geo_lat")
        lon = params.get("geo_lon")
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    except Exception:
        return None
    return None

def _inject_geo_script() -> None:
    components.html("""
        <script>
        (function () {
          function setParam(k, v) {
            try {
              const url = new URL(window.location);
              url.searchParams.set(k, v);
              window.history.replaceState({}, '', url);
            } catch (e) {}
          }
          if (!navigator.geolocation) {
            setParam('geo_err', 'unsupported');
            return;
          }
          navigator.geolocation.getCurrentPosition(function (pos) {
              setParam('geo_lat', pos.coords.latitude);
              setParam('geo_lon', pos.coords.longitude);
              setParam('geo_ts', Date.now());
          }, function (err) {
              setParam('geo_err', err && err.code ? err.code : 'denied');
          }, { enableHighAccuracy: true, maximumAge: 30000, timeout: 15000 });
        })();
        </script>
    """, height=0)

def ensure_browser_geolocation(request: bool = True) -> Optional[Tuple[float, float]]:
    q = _read_geo_from_query()
    if q:
        st.session_state["geo_lat"], st.session_state["geo_lon"] = q
        return q
    if "geo_lat" in st.session_state and "geo_lon" in st.session_state:
        try:
            return float(st.session_state["geo_lat"]), float(st.session_state["geo_lon"])
        except Exception:
            pass
    if request:
        _inject_geo_script()
    return None

def plan_route_nearest(origin: Tuple[float, float], dishes: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    remaining = [d for d in dishes if d.get("pickup_lat") and d.get("pickup_lon")]
    ordered: List[Dict[str, Any]] = []
    cur = origin
    while remaining and len(ordered) < max(1, int(limit)):
        nearest = min(remaining, key=lambda d: haversine_km(cur[0], cur[1], float(d["pickup_lat"]), float(d["pickup_lon"])))
        ordered.append(nearest)
        cur = (float(nearest["pickup_lat"]), float(nearest["pickup_lon"]))
        remaining = [d for d in remaining if d["id"] != nearest["id"]]
    return ordered

def find_nearest_hub(point: Tuple[float, float]) -> Optional[Dict[str, Any]]:
    hubs = fetch_all("SELECT * FROM hubs")
    hubs = [h for h in hubs if h.get("lat") is not None and h.get("lon") is not None]
    if not hubs:
        return None
    return min(hubs, key=lambda h: haversine_km(point[0], point[1], float(h["lat"]), float(h["lon"])))

def generate_qr_image(payload: str, dish_id: str) -> Path:
    img = qrcode.make(payload)
    path = QRCODE_DIR / f"{dish_id}.png"
    img.save(path)
    return path

def decode_qr_from_image(image_bytes: bytes) -> Optional[str]:
    if _HAS_CV2:
        try:
            arr = np_from_bytes(image_bytes)
            detector = cv2.QRCodeDetector()
            val, pts, _ = detector.detectAndDecode(arr)
            if val:
                return val
        except Exception:
            pass
    if bool(get_setting("qr_fallback_enabled", True)):
        try:
            files = {"file": ("qr.png", image_bytes, "image/png")}
            r = requests.post("https://api.qrserver.com/v1/read-qr-code/", files=files, timeout=20)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list) and data and "symbol" in data[0]:
                sym = data[0]["symbol"]
                if sym and sym[0].get("data"):
                    return sym[0]["data"]
        except Exception:
            return None
    return None

def np_from_bytes(image_bytes: bytes):
    import numpy as np
    nparr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

# ---------------------------
# Data access helpers
# ---------------------------
def fetch_one(sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row

def fetch_all(sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def execute(sql: str, params: Tuple = ()) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()

# ---------------------------
# Authentication
# ---------------------------
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return fetch_one("SELECT * FROM users WHERE email = ?", (email,))

def create_or_update_user(name: str, email: str, phone: str, roles: List[str], address: str, lat: Optional[float], lon: Optional[float]) -> Dict[str, Any]:
    u = get_user_by_email(email)
    roles_json = json.dumps(sorted(set(roles)))
    if u:
        execute("UPDATE users SET name=?, phone=?, roles=?, address=?, lat=?, lon=? WHERE email=?",
                (name, phone, roles_json, address, lat, lon, email))
        return get_user_by_email(email)
    uid = uuid()
    execute("INSERT INTO users (id, name, email, phone, roles, address, lat, lon, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (uid, name, email, phone, roles_json, address, lat, lon, now_ts()))
    return fetch_one("SELECT * FROM users WHERE id = ?", (uid,))

def has_role(user: Dict[str, Any], role: str) -> bool:
    try:
        roles = json.loads(user.get("roles") or "[]")
        return role in roles
    except Exception:
        return False

# ---------------------------
# Domain helpers
# ---------------------------
def ensure_seed_data():
    if not fetch_one("SELECT id FROM hubs LIMIT 1"):
        hid = uuid()
        execute("INSERT INTO hubs (id, name, address, lat, lon) VALUES (?,?,?,?,?)",
                (hid, "Central Hub", "Cape Town, South Africa", -33.9249, 18.4241))
    if not fetch_one("SELECT id FROM lighthouses LIMIT 1"):
        lid = uuid()
        execute("INSERT INTO lighthouses (id, name, address, lat, lon) VALUES (?,?,?,?,?)",
                (lid, "Lighthouse A", "Cape Town, South Africa", -33.93, 18.42))

def seed_dummy_data() -> Dict[str, int]:
    ensure_seed_data()
    hubs = fetch_all("SELECT * FROM hubs")
    lighthouses = fetch_all("SELECT * FROM lighthouses")
    if not hubs or not lighthouses:
        return {"users": 0, "dishes": 0, "trips": 0, "notifications": 0}
    hub = hubs[0]
    lighthouse = lighthouses[0]
    counts = {"users": 0, "dishes": 0, "trips": 0, "notifications": 0}

    alice = create_or_update_user("Alice Cook", "alice@example.org", "", ["COOK"], "Sea Point, Cape Town, South Africa", -33.915, 18.390)
    zane = create_or_update_user("Zane Cook", "zane@example.org", "", ["COOK"], "Rondebosch, Cape Town, South Africa", -33.959, 18.467)
    bob = create_or_update_user("Bob Driver", "bob@example.org", "", ["DRIVER"], "Green Point, Cape Town, South Africa", -33.904, 18.407)
    create_or_update_user("Hannah Hub", "hannah@example.org", "", ["HUB"], "Cape Town, South Africa", -33.924, 18.424)
    create_or_update_user("Liam Light", "liam@example.org", "", ["LIGHTHOUSE"], "Woodstock, Cape Town, South Africa", -33.930, 18.448)
    counts["users"] = 5

    trip = create_trip(bob["id"])
    counts["trips"] = 1

    dishes: List[Dict[str, Any]] = []
    dishes.append(create_dish(alice["id"], "Chicken Casserole", "Hearty baked casserole", ["Celery"], 4, date.today(), date.today(), "Sea Point, Cape Town", -33.915, 18.390))
    dishes.append(create_dish(alice["id"], "Veg Pasta Bake", "Cheesy pasta bake", ["Milk", "Gluten"], 6, date.today(), date.today(), "Sea Point, Cape Town", -33.915, 18.390))
    dishes.append(create_dish(zane["id"], "Beef Stew", "Slow-cooked stew", [], 5, date.today(), None, "Rondebosch, Cape Town", -33.959, 18.467))
    dishes.append(create_dish(zane["id"], "Lentil Soup", "Vegan soup", [], 8, date.today(), date.today(), "Rondebosch, Cape Town", -33.959, 18.467))
    counts["dishes"] = len(dishes)

    d2 = dishes[1]
    update_dish_status_by_qr(d2["qr_payload"], "picked_up", trip_id=trip["id"])
    update_dish_status_by_qr(d2["qr_payload"], "at_hub", hub_id=hub["id"])
    update_dish_status_by_qr(d2["qr_payload"], "assigned_to_lighthouse", hub_id=hub["id"], lighthouse_id=lighthouse["id"])
    update_dish_status_by_qr(d2["qr_payload"], "at_lighthouse", lighthouse_id=lighthouse["id"])
    upd = update_dish_status_by_qr(d2["qr_payload"], "distributed", lighthouse_id=lighthouse["id"])
    if upd:
        create_notification(upd["cook_id"], upd["id"], f"Your dish '{upd['title']}' has been distributed. Thank you!", "distributed")
        counts["notifications"] += 1

    d3 = dishes[2]
    update_dish_status_by_qr(d3["qr_payload"], "picked_up", trip_id=trip["id"])
    update_dish_status_by_qr(d3["qr_payload"], "at_hub", hub_id=hub["id"])
    return counts

def create_dish(cook_id: str, title: str, description: str, allergens: List[str], portions: int, prepared_at: date, expiry_date: Optional[date], pickup_address: str, pickup_lat: Optional[float], pickup_lon: Optional[float]) -> Dict[str, Any]:
    dish_id = uuid()
    allergen_csv = ",".join(allergens)
    payload = f"JOM1|{dish_id}"
    qr_path = generate_qr_image(payload, dish_id)
    execute("""
        INSERT INTO dishes (id, cook_id, title, description, allergens, portions, prepared_at, expiry_date, status, pickup_address, pickup_lat, pickup_lon, qr_payload, qr_path)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (dish_id, cook_id, title, description, allergen_csv, portions, prepared_at.isoformat(), expiry_date.isoformat() if expiry_date else None, "prepared", pickup_address, pickup_lat, pickup_lon, payload, str(qr_path)))
    return fetch_one("SELECT * FROM dishes WHERE id = ?", (dish_id,))

def update_dish_status_by_qr(qr_payload: str, new_status: str, trip_id: Optional[str] = None, hub_id: Optional[str] = None, lighthouse_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not qr_payload or not qr_payload.startswith("JOM1|"):
        return None
    dish_id = qr_payload.split("|")[1]
    dish = fetch_one("SELECT * FROM dishes WHERE id = ?", (dish_id,))
    if not dish:
        return None
    execute("UPDATE dishes SET status=?, trip_id=COALESCE(?, trip_id), hub_id=COALESCE(?, hub_id), lighthouse_id=COALESCE(?, lighthouse_id) WHERE id=?",
            (new_status, trip_id, hub_id, lighthouse_id, dish_id))
    return fetch_one("SELECT * FROM dishes WHERE id = ?", (dish_id,))

def create_trip(driver_id: str) -> Dict[str, Any]:
    tid = uuid()
    execute("INSERT INTO trips (id, driver_id, started_at, status) VALUES (?,?,?,?)", (tid, driver_id, now_ts(), "active"))
    return fetch_one("SELECT * FROM trips WHERE id = ?", (tid,))

def end_trip(trip_id: str) -> None:
    execute("UPDATE trips SET status='completed', ended_at=? WHERE id=?", (now_ts(), trip_id))

def create_notification(user_id: str, dish_id: Optional[str], message: str, type_: str = "info"):
    nid = uuid()
    execute("INSERT INTO notifications (id, user_id, dish_id, type, message, created_at, read) VALUES (?,?,?,?,?,?,0)",
            (nid, user_id, dish_id, type_, message, now_ts()))

def award_badges(user_id: str) -> List[str]:
    cooked = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE cook_id=?", (user_id,))["c"]
    picked = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE trip_id IN (SELECT id FROM trips WHERE driver_id=?)", (user_id,))["c"]
    distributed = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE cook_id=? AND status='distributed'", (user_id,))["c"]
    badges = []
    if cooked >= 1:
        badges.append("🍳 First Cook")
    if cooked >= 10:
        badges.append("👨‍🍳 Home Chef 10")
    if picked >= 1:
        badges.append("🚗 First Pickup")
    if picked >= 20:
        badges.append("🏆 Road Hero 20")
    if distributed >= 1:
        badges.append("💚 Impact Maker")
    return badges

# ---------------------------
# UI Components
# ---------------------------
def render_status_badge(status: str) -> str:
    status_display = {
        "prepared": "Prepared",
        "picked_up": "Picked Up",
        "at_hub": "At Hub",
        "assigned_to_lighthouse": "Assigned",
        "at_lighthouse": "At Lighthouse",
        "distributed": "Distributed"
    }
    return f'<span class="status-badge status-{status}">{status_display.get(status, status)}</span>'

def header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"🍲 {APP_NAME}")
        st.caption(APP_TAGLINE)
    with col2:
        user = st.session_state.get("user")
        if user:
            st.write(f"👤 **{user.get('name', 'User')}**")
            if st.button("Sign Out", key="signout_btn", use_container_width=True):
                st.session_state.clear()
                st.rerun()

    user = st.session_state.get("user")
    pages = visible_pages_for_user(user)
    
    if pages:
        cols = st.columns(len(pages))
        for i, page_name in enumerate(pages):
            current = st.session_state.get("page", "Home")
            btn_type = "primary" if page_name == current else "secondary"
            if cols[i].button(page_name, key=f"nav_{page_name}", use_container_width=True, type=btn_type if page_name == current else "secondary"):
                st.session_state["page"] = page_name
                st.rerun()
    
    st.divider()

def goto(page: str):
    st.session_state["page"] = page
    st.rerun()

def page_allowed(user: Dict[str, Any], page: str) -> bool:
    role_map = {"Cook": "COOK", "Driver": "DRIVER", "Hub": "HUB", "Lighthouse": "LIGHTHOUSE"}
    if page in ("Home", "Profile", "Safety Guide", "Settings", "Admin"):
        return True
    req = role_map.get(page)
    if req:
        return has_role(user, req)
    return True

def visible_pages_for_user(user: Optional[Dict[str, Any]]) -> List[str]:
    if not user:
        return ["Home", "Sign Up", "Sign In", "Safety Guide"]
    
    pages: List[str] = ["Home"]
    if has_role(user, "COOK"):
        pages.append("Cook")
    if has_role(user, "DRIVER"):
        pages.append("Driver")
    if has_role(user, "HUB"):
        pages.append("Hub")
    if has_role(user, "LIGHTHOUSE"):
        pages.append("Lighthouse")
    pages += ["Profile", "Safety Guide", "Settings", "Admin"]
    return pages

# ---------------------------
# Pages
# ---------------------------
def home_page():
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 🌟 Welcome to JustOneMore")
        st.markdown("""
        Transform your surplus into support for those who need it most. Our platform connects 
        generous cooks with dedicated drivers, distribution hubs, and community lighthouses 
        to ensure no meal goes to waste.
        
        ### How It Works
        
        **🍳 For Cooks**  
        Log your prepared dishes, mark allergens, and generate a unique QR code label.
        
        **🚗 For Drivers**  
        Start a trip, view nearby pickups on an interactive map, and scan QR codes to collect dishes.
        
        **🏢 For Hubs**  
        Receive donations, manage inventory, and assign dishes to community lighthouses.
        
        **🏠 For Lighthouses**  
        Scan arrivals, distribute to those in need, and notify cooks of their impact.
        """)
    
    with col2:
        user = st.session_state.get("user")
        if not user:
            st.markdown("### Get Started")
            st.info("Create an account or sign in to begin making a difference.")
            if st.button("🚀 Sign Up Now", type="primary", use_container_width=True):
                goto("Sign Up")
            if st.button("👋 Sign In", use_container_width=True):
                goto("Sign In")
        else:
            st.markdown("### Quick Actions")
            if has_role(user, "COOK"):
                if st.button("🍳 Log a Dish", type="primary", use_container_width=True):
                    goto("Cook")
            if has_role(user, "DRIVER"):
                if st.button("🚗 Start Trip", type="primary", use_container_width=True):
                    goto("Driver")
            if st.button("📊 View My Profile", use_container_width=True):
                goto("Profile")
            
            st.markdown("### My Impact")
            cooked = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE cook_id=?", (user["id"],))["c"]
            distributed = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE cook_id=? AND status='distributed'", (user["id"],))["c"]
            st.metric("Dishes Contributed", cooked)
            st.metric("Meals Distributed", distributed * 4)
    
    st.divider()
    
    # Platform statistics
    st.markdown("### 📈 Platform Impact")
    col1, col2, col3, col4 = st.columns(4)
    
    total_users = fetch_one("SELECT COUNT(*) AS c FROM users")["c"]
    total_dishes = fetch_one("SELECT COUNT(*) AS c FROM dishes")["c"]
    total_portions = fetch_one("SELECT COALESCE(SUM(portions),0) AS s FROM dishes")["s"]
    distributed_dishes = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE status='distributed'")["c"]
    
    col1.metric("👥 Active Users", total_users)
    col2.metric("🍽️ Total Dishes", total_dishes)
    col3.metric("🥘 Portions Logged", total_portions)
    col4.metric("✅ Distributed", distributed_dishes)

def sign_up_page():
    user = st.session_state.get("user")
    if user:
        st.success(f"✅ You're already signed in as **{user.get('name', 'User')}**")
        st.info("Use the navigation above to access features.")
        return
    
    st.markdown("## 📝 Create Your Account")
    st.markdown("Join our community and start making a difference today.")
    
    with st.form("signup_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", placeholder="John Doe")
            email = st.text_input("Email Address *", placeholder="john@example.com")
            phone = st.text_input("Phone Number", placeholder="+27 123 456 789")
        
        with col2:
            st.markdown("**Select Your Roles** *")
            st.caption("Choose all that apply")
            role_cook = st.checkbox("🍳 Cook - I want to donate meals", value=True)
            role_driver = st.checkbox("🚗 Driver - I can collect and deliver")
            role_hub = st.checkbox("🏢 Hub Manager - I manage a collection point")
            role_lighthouse = st.checkbox("🏠 Lighthouse - I distribute to those in need")
        
        st.markdown("---")
        st.markdown("**📍 Location Information**")
        address = st.text_input("Address", placeholder="123 Main Street, Cape Town, South Africa")
        
        col_geo1, col_geo2 = st.columns([3, 1])
        with col_geo1:
            st.caption("We'll use this to show you nearby opportunities")
        with col_geo2:
            geocode_btn = st.form_submit_button("🌍 Geocode", use_container_width=True)
        
        lat, lon = None, None
        if geocode_btn and address:
            with st.spinner("🔍 Finding your location..."):
                coords = geocode_address(address)
            if coords:
                st.success(f"✅ Location found: {coords[0]:.5f}, {coords[1]:.5f}")
                lat, lon = coords
            else:
                st.warning("⚠️ Could not find location. You can still sign up.")
        
        st.markdown("---")
        submit = st.form_submit_button("✨ Create Account", type="primary", use_container_width=True)
    
    if submit:
        if not name or not email:
            st.error("❌ Please provide both name and email address.")
            return
        
        roles = []
        if role_cook:
            roles.append("COOK")
        if role_driver:
            roles.append("DRIVER")
        if role_hub:
            roles.append("HUB")
        if role_lighthouse:
            roles.append("LIGHTHOUSE")
        
        if not roles:
            st.error("❌ Please select at least one role.")
            return
        
        try:
            user = create_or_update_user(name, email, phone, roles, address, lat, lon)
            st.session_state["user"] = user
            st.success("✅ Account created successfully! Welcome to JustOneMore!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error creating account: {str(e)}")

def sign_in_page():
    user = st.session_state.get("user")
    if user:
        st.success(f"✅ You're already signed in as **{user.get('name', 'User')}**")
        st.info("Use the navigation above to access features.")
        return
    
    st.markdown("## 👋 Welcome Back")
    st.markdown("Sign in to continue making an impact.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("signin_form"):
            email = st.text_input("Email Address", placeholder="your@email.com")
            submit = st.form_submit_button("🔐 Sign In", type="primary", use_container_width=True)
        
        if submit:
            if not email:
                st.error("❌ Please enter your email address.")
                return
            
            user = get_user_by_email(email)
            if user:
                st.session_state["user"] = user
                st.success("✅ Signed in successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ No account found with that email. Please sign up first.")
    
    with col2:
        st.info("**New here?**\n\nCreate an account to start contributing to your community.")
        if st.button("📝 Sign Up", use_container_width=True):
            goto("Sign Up")

def cook_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please sign in to access this page.")
        if st.button("Go to Sign In"):
            goto("Sign In")
        return
    
    if not has_role(user, "COOK"):
        st.warning("⚠️ You need the COOK role to access this page.")
        st.info("You can add this role by updating your profile on the Sign Up page.")
        return
    
    st.markdown("## 🍳 Log a New Dish")
    
    with st.form("dish_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            title = st.text_input("Dish Name *", placeholder="e.g., Vegetable Curry")
            description = st.text_area("Description", placeholder="Brief description of the dish...", height=100)
            allergens = st.multiselect("🔴 Allergens Present", ALLERGENS, help="Select all allergens in this dish")
        
        with col2:
            portions = st.number_input("Number of Portions *", min_value=1, max_value=100, value=4)
            prepared = st.date_input("Prepared On *", value=date.today())
            expiry_enabled = st.checkbox("Add Best Before Date")
            expiry = st.date_input("Best Before", value=date.today()) if expiry_enabled else None
        
        st.markdown("---")
        st.markdown("**📍 Pickup Location**")
        
        col_addr1, col_addr2 = st.columns([3, 1])
        with col_addr1:
            pickup_address = st.text_input("Pickup Address", value=user.get("address") or "", placeholder="Where can drivers collect this?")
        with col_addr2:
            use_saved = st.checkbox("Use my saved location", value=True)
        
        lat, lon = None, None
        if use_saved and user.get("lat") and user.get("lon"):
            lat, lon = float(user["lat"]), float(user["lon"])
            st.caption(f"Using saved coordinates: {lat:.5f}, {lon:.5f}")
        elif pickup_address:
            if st.form_submit_button("🌍 Geocode Address"):
                with st.spinner("Finding location..."):
                    coords = geocode_address(pickup_address)
                if coords:
                    st.success(f"✅ Found: {coords[0]:.5f}, {coords[1]:.5f}")
                    lat, lon = coords
                else:
                    st.warning("Could not geocode. Dish will be created without coordinates.")
        
        st.markdown("---")
        submit = st.form_submit_button("✨ Create Dish & Generate QR", type="primary", use_container_width=True)
    
    if submit:
        if not title:
            st.error("❌ Please provide a dish name.")
            return
        
        dish = create_dish(user["id"], title, description, allergens, int(portions), prepared, 
                          expiry if isinstance(expiry, date) else None, pickup_address, lat, lon)
        
        st.success("✅ Dish created successfully!")
        
        col_qr1, col_qr2 = st.columns([1, 2])
        with col_qr1:
            if dish.get("qr_path"):
                st.image(str(dish["qr_path"]), caption="Your QR Code", width=300)
                with open(dish["qr_path"], "rb") as f:
                    st.download_button("📥 Download QR Code", f, file_name=f"{dish['id']}.png", 
                                     mime="image/png", use_container_width=True)
        with col_qr2:
            st.markdown("### Next Steps")
            st.markdown("""
            1. **Print** the QR code
            2. **Attach** it to your dish container
            3. **Wait** for a driver to collect
            4. **Get notified** when it's distributed!
            """)
            st.code(dish["qr_payload"], language="text")
    
    st.divider()
    st.markdown("## 📋 My Dishes")
    
    rows = fetch_all("SELECT * FROM dishes WHERE cook_id=? ORDER BY prepared_at DESC", (user["id"],))
    if rows:
        for dish in rows:
            with st.expander(f"**{dish['title']}** - {render_status_badge(dish['status'])}", expanded=False):
                col1, col2, col3 = st.columns(3)
                col1.metric("Portions", dish['portions'])
                col2.metric("Prepared", dish['prepared_at'])
                if dish.get('expiry_date'):
                    col3.metric("Best Before", dish['expiry_date'])
                
                if dish.get('description'):
                    st.markdown(f"**Description:** {dish['description']}")
                if dish.get('allergens'):
                    st.markdown(f"**Allergens:** {dish['allergens']}")
                st.markdown(f"**Pickup:** {dish.get('pickup_address', 'Not specified')}")
    else:
        st.info("📭 You haven't logged any dishes yet. Create your first one above!")

def driver_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please sign in to access this page.")
        if st.button("Go to Sign In"):
            goto("Sign In")
        return
    
    if not has_role(user, "DRIVER"):
        st.info("ℹ️ You need the DRIVER role to access this page.")
        if st.button("Add DRIVER role to my profile"):
            roles = json.loads(user["roles"])
            roles.append("DRIVER")
            user = create_or_update_user(user["name"], user["email"], user.get("phone") or "", 
                                        roles, user.get("address") or "", user.get("lat"), user.get("lon"))
            st.session_state["user"] = user
            st.success("✅ Driver role added!")
            st.rerun()
        return
    
    st.markdown("## 🚗 Driver Dashboard")
    
    active_trip = st.session_state.get("active_trip")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if not active_trip:
            st.info("No active trip. Start one to begin collecting dishes.")
        else:
            st.success(f"✅ Trip active since {active_trip['started_at'][:16]}")
    with col2:
        if not active_trip:
            if st.button("🚀 Start Trip", type="primary", use_container_width=True):
                trip = create_trip(user["id"])
                st.session_state["active_trip"] = trip
                st.rerun()
        else:
            if st.button("🛑 End Trip", use_container_width=True):
                end_trip(active_trip["id"])
                st.session_state["active_trip"] = None
                st.success("Trip ended successfully!")
                st.rerun()
    
    if not active_trip:
        return
    
    st.divider()
    st.markdown("### 📍 Your Current Location")
    
    origin: Optional[Tuple[float, float]] = None
    location_method = st.radio("", ["📱 Use my current location", "📝 Enter address manually"], 
                              horizontal=True, label_visibility="collapsed")
    
    if location_method == "📱 Use my current location":
        origin = ensure_browser_geolocation(request=True)
        col_loc1, col_loc2 = st.columns([1, 3])
        with col_loc1:
            if st.button("🔄 Refresh Location"):
                _inject_geo_script()
                st.rerun()
        with col_loc2:
            if origin:
                st.success(f"✅ Location: {origin[0]:.5f}, {origin[1]:.5f}")
            else:
                st.info("ℹ️ Allow location access in your browser to continue")
    else:
        curr_addr = st.text_input("Current Address", value=st.session_state.get("origin_address", ""))
        if st.button("🌍 Use This Address"):
            if curr_addr:
                with st.spinner("Geocoding..."):
                    coords = geocode_address(curr_addr)
                if coords:
                    st.session_state["origin_address"] = curr_addr
                    st.session_state["origin_manual"] = coords
                    origin = coords
                    st.success(f"✅ Location set: {coords[0]:.5f}, {coords[1]:.5f}")
                    st.session_state.pop("geo_lat", None)
                    st.session_state.pop("geo_lon", None)
                else:
                    st.warning("Could not find that address")
        elif "origin_manual" in st.session_state:
            origin = st.session_state["origin_manual"]
    
    st.divider()
    st.markdown("### 🍽️ Available Pickups")
    
    pickups = fetch_all("SELECT * FROM dishes WHERE status='prepared'")
    if not pickups:
        st.info("📭 No dishes available for pickup right now.")
        return
    
    for d in pickups:
        d["distance_km"] = None
        if origin and d.get("pickup_lat") and d.get("pickup_lon"):
            d["distance_km"] = round(haversine_km(origin[0], origin[1], d["pickup_lat"], d["pickup_lon"]), 2)
    pickups.sort(key=lambda x: (9999 if x["distance_km"] is None else x["distance_km"]))
    
    map_rows = [r for r in pickups if r.get("pickup_lat") and r.get("pickup_lon")]
    if map_rows:
        df = pd.DataFrame([{"lat": r["pickup_lat"], "lon": r["pickup_lon"]} for r in map_rows])
        st.map(df, zoom=11)
        
        if origin:
            st.markdown("### 🗺️ Route Planning")
            route_count = st.slider("Maximum pickups to include", 1, min(len(map_rows), 15), min(8, len(map_rows)))
            
            if st.button("📍 Plan Optimal Route", type="primary"):
                ordered = plan_route_nearest(origin, map_rows, int(route_count))
                st.session_state["route_plan_ids"] = [d["id"] for d in ordered]
                st.session_state["route_plan_origin"] = origin
            
            route_ids = st.session_state.get("route_plan_ids")
            if route_ids:
                id_to_dish = {d["id"]: d for d in pickups if d.get("pickup_lat") and d.get("pickup_lon")}
                plan_dishes = [id_to_dish[i] for i in route_ids if i in id_to_dish]
                
                if plan_dishes:
                    last_stop = (float(plan_dishes[-1]["pickup_lat"]), float(plan_dishes[-1]["pickup_lon"]))
                    hub = find_nearest_hub(last_stop) or (find_nearest_hub(origin) if origin else None)
                    
                    waypoints = [(float(d["pickup_lat"]), float(d["pickup_lon"])) for d in plan_dishes]
                    if hub:
                        multi_link = gmaps_multi_stop_link(origin, waypoints, (float(hub["lat"]), float(hub["lon"])))
                        st.link_button("🗺️ Open Route in Google Maps", multi_link, use_container_width=True)
                    
                    total_km = 0.0
                    curr = origin
                    st.markdown("**Route Overview:**")
                    for idx, d in enumerate(plan_dishes, start=1):
                        nxt = (float(d["pickup_lat"]), float(d["pickup_lon"]))
                        if curr:
                            leg_km = haversine_km(curr[0], curr[1], nxt[0], nxt[1])
                            total_km += leg_km
                        st.markdown(f"{idx}. **{d['title']}** ({d['portions']} portions) - {leg_km:.1f} km")
                        curr = nxt
                    
                    if hub:
                        final_km = haversine_km(curr[0], curr[1], float(hub["lat"]), float(hub["lon"]))
                        total_km += final_km
                        st.markdown(f"→ **{hub['name']}** - {final_km:.1f} km")
                    
                    st.metric("Total Route Distance", f"{total_km:.1f} km")
                    
                    first = plan_dishes[0]
                    next_link = google_maps_dir_link(origin, (float(first["pickup_lat"]), float(first["pickup_lon"])))
                    st.link_button("🚗 Navigate to First Pickup", next_link, use_container_width=True)
    
    st.divider()
    st.markdown("### 📦 Pickup Dishes")
    
    for dish in pickups[:10]:
        with st.expander(f"**{dish['title']}** ({dish['portions']} portions) - {dish.get('distance_km', '?')} km away"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Allergens:** {dish.get('allergens') or 'None'}")
                st.markdown(f"**Pickup:** {dish.get('pickup_address', 'Not specified')}")
                if dish.get("pickup_lat") and dish.get("pickup_lon"):
                    link = google_maps_dir_link(origin, (dish["pickup_lat"], dish["pickup_lon"]))
                    st.link_button("🗺️ Navigate", link, use_container_width=True)
            
            with col2:
                st.markdown("**Scan QR to Confirm**")
                img = st.camera_input("", key=f"cam_pick_{dish['id']}", label_visibility="collapsed")
                if img is not None:
                    payload = decode_qr_from_image(img.getvalue())
                    if payload:
                        updated = update_dish_status_by_qr(payload, "picked_up", trip_id=active_trip["id"])
                        if updated:
                            st.success("✅ Pickup confirmed!")
                            st.rerun()
                    else:
                        st.warning("Could not read QR")
                
                manual = st.text_input("Or enter code:", key=f"manual_pick_{dish['id']}", label_visibility="collapsed")
                if st.button("Confirm", key=f"btn_pick_{dish['id']}", use_container_width=True):
                    if manual:
                        updated = update_dish_status_by_qr(manual.strip(), "picked_up", trip_id=active_trip["id"])
                        if updated:
                            st.success("✅ Pickup confirmed!")
                            st.rerun()
    
    st.divider()
    st.markdown("### 🏢 Drop-off at Hub")
    hubs = fetch_all("SELECT * FROM hubs")
    if hubs:
        hub = hubs[0]
        if origin:
            hubs_sorted = sorted(hubs, key=lambda h: haversine_km(origin[0], origin[1], h["lat"], h["lon"]) 
                               if h.get("lat") and h.get("lon") else 9999)
            hub = hubs_sorted[0]
        
        st.info(f"📍 Nearest Hub: **{hub['name']}** - {hub.get('address', '')}")
        if hub.get("lat") and hub.get("lon"):
            st.link_button("🗺️ Navigate to Hub", google_maps_dir_link(origin, (hub["lat"], hub["lon"])), 
                          use_container_width=True)
        
        st.markdown("**Scan each dish at hub:**")
        img = st.camera_input("Hub Intake QR", key="hub_intake_cam")
        if img is not None:
            payload = decode_qr_from_image(img.getvalue())
            if payload:
                updated = update_dish_status_by_qr(payload, "at_hub", hub_id=hub["id"])
                if updated:
                    st.success("✅ Hub intake recorded!")
                    st.rerun()
            else:
                st.warning("Could not decode QR")

def hub_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please sign in to access this page.")
        if st.button("Go to Sign In"):
            goto("Sign In")
        return
    
    st.markdown("## 🏢 Hub Management")
    
    hubs = fetch_all("SELECT * FROM hubs")
    if not hubs:
        st.error("❌ No hubs configured. Use Admin page to set up hubs.")
        return
    
    hub_names = {h["name"]: h for h in hubs}
    hub_name = st.selectbox("Select Your Hub", list(hub_names))
    hub = hub_names[hub_name]
    
    st.markdown(f"### Managing: **{hub['name']}**")
    st.caption(hub.get('address', 'No address'))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Intake Scanning")
        st.caption("Mark dishes as arrived at hub")
        img = st.camera_input("Scan Dish QR", key="hub_intake")
        if img is not None:
            payload = decode_qr_from_image(img.getvalue())
            if payload:
                updated = update_dish_status_by_qr(payload, "at_hub", hub_id=hub["id"])
                if updated:
                    st.success(f"✅ {updated['title']} marked as at hub!")
                    st.rerun()
            else:
                st.warning("Could not decode QR")
    
    with col2:
        st.markdown("#### 🏠 Assign to Lighthouse")
        lighthouses = fetch_all("SELECT * FROM lighthouses")
        if not lighthouses:
            st.error("No lighthouses configured")
        else:
            lh_names = {l["name"]: l for l in lighthouses}
            lh_name = st.selectbox("Select Lighthouse", list(lh_names))
            lighthouse = lh_names[lh_name]
            
            rows = fetch_all("SELECT * FROM dishes WHERE status='at_hub' AND (hub_id=? OR hub_id IS NULL)", (hub["id"],))
            if rows:
                sel = st.multiselect("Select Dishes", [f"{r['title']} - {r['portions']} portions" for r in rows])
                sel_ids = [r["id"] for r in rows if f"{r['title']} - {r['portions']} portions" in sel]
                
                if st.button("✅ Assign Selected", type="primary", disabled=not sel_ids):
                    for did in sel_ids:
                        execute("UPDATE dishes SET status='assigned_to_lighthouse', lighthouse_id=?, hub_id=? WHERE id=?", 
                               (lighthouse["id"], hub["id"], did))
                    st.success(f"✅ Assigned {len(sel_ids)} dish(es) to {lighthouse['name']}")
                    st.rerun()
            else:
                st.info("📭 No dishes at hub currently")
    
    st.divider()
    st.markdown("### 📊 Hub Inventory")
    inventory = fetch_all("SELECT * FROM dishes WHERE hub_id=? AND status IN ('at_hub', 'assigned_to_lighthouse')", (hub["id"],))
    if inventory:
        for dish in inventory:
            status_html = render_status_badge(dish['status'])
            st.markdown(f"**{dish['title']}** ({dish['portions']} portions) - {status_html}", unsafe_allow_html=True)
    else:
        st.info("Empty inventory")

def lighthouse_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please sign in to access this page.")
        if st.button("Go to Sign In"):
            goto("Sign In")
        return
    
    st.markdown("## 🏠 Lighthouse Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Mark Arrival")
        st.caption("Scan when dishes arrive at your lighthouse")
        img1 = st.camera_input("Scan Arrival QR", key="lh_arrival")
        if img1 is not None:
            payload = decode_qr_from_image(img1.getvalue())
            if payload:
                updated = update_dish_status_by_qr(payload, "at_lighthouse")
                if updated:
                    st.success(f"✅ {updated['title']} arrival recorded!")
                    st.rerun()
            else:
                st.warning("Could not decode QR")
    
    with col2:
        st.markdown("### ✅ Mark Distribution")
        st.caption("Scan when distributing to recipients")
        img2 = st.camera_input("Scan Distribution QR", key="lh_distrib")
        if img2 is not None:
            payload = decode_qr_from_image(img2.getvalue())
            if payload:
                updated = update_dish_status_by_qr(payload, "distributed")
                if updated:
                    cook_id = updated.get("cook_id")
                    if cook_id:
                        create_notification(cook_id, updated["id"], 
                                          f"Your dish '{updated['title']}' has been distributed. Thank you for your contribution!", 
                                          "distributed")
                    st.success(f"✅ {updated['title']} distributed and cook notified!")
                    st.balloons()
                    st.rerun()
            else:
                st.warning("Could not decode QR")
    
    st.divider()
    st.markdown("### 📦 Current Inventory")
    inventory = fetch_all("SELECT * FROM dishes WHERE status IN ('assigned_to_lighthouse', 'at_lighthouse')")
    if inventory:
        for dish in inventory:
            status_html = render_status_badge(dish['status'])
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{dish['title']}** - {status_html}", unsafe_allow_html=True)
                st.caption(f"{dish['portions']} portions | Allergens: {dish.get('allergens', 'None')}")
            with col_b:
                st.metric("Status", dish['status'].replace('_', ' ').title())
    else:
        st.info("📭 No dishes currently assigned or at lighthouse")

def profile_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please sign in to access this page.")
        if st.button("Go to Sign In"):
            goto("Sign In")
        return
    
    st.markdown("## 👤 My Profile")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Personal Information")
        st.markdown(f"**Name:** {user['name']}")
        st.markdown(f"**Email:** {user.get('email', 'Not provided')}")
        st.markdown(f"**Phone:** {user.get('phone', 'Not provided')}")
        
        roles = json.loads(user.get('roles', '[]'))
        role_icons = {"COOK": "🍳", "DRIVER": "🚗", "HUB": "🏢", "LIGHTHOUSE": "🏠"}
        role_display = [f"{role_icons.get(r, '')} {r}" for r in roles]
        st.markdown(f"**Roles:** {', '.join(role_display)}")
        
        if user.get("address"):
            st.markdown(f"**Location:** {user['address']}")
            if user.get("lat") and user.get("lon"):
                st.caption(f"Coordinates: {float(user['lat']):.5f}, {float(user['lon']):.5f}")
    
    with col2:
        st.markdown("### Quick Actions")
        if has_role(user, "COOK"):
            if st.button("🍳 Log a Dish", use_container_width=True):
                goto("Cook")
        if has_role(user, "DRIVER"):
            if st.button("🚗 Start Trip", use_container_width=True):
                goto("Driver")
        if st.button("⚙️ Settings", use_container_width=True):
            goto("Settings")
    
    st.divider()
    
    # Statistics
    st.markdown("### 📊 My Impact")
    
    cooked = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE cook_id=?", (user["id"],))["c"]
    picked = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE trip_id IN (SELECT id FROM trips WHERE driver_id=?)", (user["id"],))["c"]
    distributed = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE cook_id=? AND status='distributed'", (user["id"],))["c"]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🍳 Dishes Cooked", cooked)
    col2.metric("🚗 Pickups Driven", picked)
    col3.metric("✅ Distributed", distributed)
    
    points = cooked * 10 + picked * 5 + distributed * 8
    col4.metric("⭐ Points", points)
    
    # Badges
    st.markdown("### 🏆 Badges & Achievements")
    badges = award_badges(user["id"])
    if badges:
        badge_html = '<div class="badge-container">'
        for badge in badges:
            badge_html += f'<span class="badge">{badge}</span>'
        badge_html += '</div>'
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.info("Complete actions to earn badges!")
    
    st.divider()
    
    # Notifications
    st.markdown("### 🔔 Recent Notifications")
    notes = fetch_all("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 10", (user["id"],))
    if notes:
        for n in notes:
            note_type_icon = {"distributed": "✅", "info": "ℹ️", "warning": "⚠️"}
            icon = note_type_icon.get(n['type'], "📌")
            timestamp = n['created_at'][:16].replace('T', ' ')
            st.info(f"{icon} **{timestamp}** - {n['message']}")
    else:
        st.info("📭 No notifications yet")
    
    st.divider()
    
    # Data export
    st.markdown("### 📥 Export My Data")
    col1, col2 = st.columns(2)
    
    with col1:
        my_dishes = fetch_all("SELECT * FROM dishes WHERE cook_id=? ORDER BY prepared_at DESC", (user["id"],))
        if my_dishes:
            df_d = pd.DataFrame(my_dishes)
            csv_dishes = df_d.to_csv(index=False).encode("utf-8")
            st.download_button("📄 Download My Dishes (CSV)", csv_dishes, 
                             file_name="my_dishes.csv", mime="text/csv", use_container_width=True)
        else:
            st.button("📄 No Dishes to Export", disabled=True, use_container_width=True)
    
    with col2:
        my_trips = fetch_all("SELECT * FROM trips WHERE driver_id=? ORDER BY started_at DESC", (user["id"],))
        if my_trips:
            df_t = pd.DataFrame(my_trips)
            csv_trips = df_t.to_csv(index=False).encode("utf-8")
            st.download_button("🚗 Download My Trips (CSV)", csv_trips, 
                             file_name="my_trips.csv", mime="text/csv", use_container_width=True)
        else:
            st.button("🚗 No Trips to Export", disabled=True, use_container_width=True)

def safety_guide_page():
    st.markdown("## 🛡️ Food Safety Guide")
    st.markdown("*Ensuring every meal is safe and nutritious*")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔥 Cooking & Preparation")
        st.markdown("""
        **Temperature Control**
        - Cook food thoroughly (minimum 74°C/165°F internal temperature)
        - Cool quickly within 2 hours of cooking
        - Refrigerate at 4°C (40°F) or below
        - Freeze at -18°C (0°F) or below
        
        **Hygiene Essentials**
        - Wash hands thoroughly before and during cooking
        - Sanitize all work surfaces
        - Use separate cutting boards for raw and cooked foods
        - Clean utensils between different food types
        """)
        
        st.markdown("### 📦 Packaging & Labeling")
        st.markdown("""
        **Container Requirements**
        - Use food-grade, clean containers
        - Ensure airtight seals
        - Label with dish name and date
        - Attach the QR code securely
        
        **Required Information**
        - Dish name and description
        - Preparation date
        - Best before date (if applicable)
        - Complete allergen list
        - Number of portions
        """)
    
    with col2:
        st.markdown("### 🚗 Transportation")
        st.markdown("""
        **Temperature Maintenance**
        - Use insulated coolers for transport
        - Add ice packs for cold items
        - Keep hot foods above 60°C (140°F)
        - Minimize time in temperature danger zone (4-60°C)
        
        **Safe Handling**
        - Secure containers to prevent spills
        - Transport promptly after pickup
        - Avoid cross-contamination
        - Keep raw and cooked foods separate
        """)
        
        st.markdown("### ♨️ Reheating & Service")
        st.markdown("""
        **Safe Reheating**
        - Reheat to minimum 74°C (165°F)
        - Use food thermometer to verify
        - Stir during reheating for even temperature
        - Never reheat more than once
        
        **Distribution Guidelines**
        - Serve immediately after reheating
        - Keep hot foods hot, cold foods cold
        - Discard food left at room temperature over 2 hours
        - Never refreeze previously thawed food
        """)
    
    st.divider()
    
    st.markdown("### 🔴 Allergen Management")
    st.markdown("""
    The 14 major allergens must be clearly labeled on all dishes:
    """)
    
    allergen_cols = st.columns(7)
    for i, allergen in enumerate(ALLERGENS):
        allergen_cols[i % 7].markdown(f"• {allergen}")
    
    st.warning("⚠️ **Important:** Always verify allergen information is accurate and clearly labeled.")
    
    st.divider()
    
    st.markdown("### ✅ Daily Checklist")
    
    checklist = {
        "Before Cooking": [
            "Wash hands thoroughly",
            "Sanitize work surfaces",
            "Check ingredient freshness",
            "Ensure proper ventilation"
        ],
        "During Cooking": [
            "Use food thermometer",
            "Prevent cross-contamination",
            "Taste with clean utensils",
            "Monitor cooking times"
        ],
        "After Cooking": [
            "Cool food properly",
            "Package in clean containers",
            "Label with all required info",
            "Store at correct temperature"
        ]
    }
    
    cols = st.columns(3)
    for idx, (phase, items) in enumerate(checklist.items()):
        with cols[idx]:
            st.markdown(f"**{phase}**")
            for item in items:
                st.checkbox(item, key=f"check_{phase}_{item}")

def settings_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please sign in to access this page.")
        if st.button("Go to Sign In"):
            goto("Sign In")
        return
    
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["🔧 Application", "👤 Profile", "🔐 Privacy"])
    
    with tab1:
        st.markdown("### Application Settings")
        cfg = load_settings()
        
        with st.form("settings_form"):
            st.markdown("**Geocoding Configuration**")
            ua = st.text_input("User-Agent for geocoding requests", 
                             value=str(cfg.get("user_agent", USER_AGENT)),
                             help="Include your contact email or domain")
            
            st.markdown("**QR Code Settings**")
            qr_fb = st.checkbox("Enable remote QR decoding fallback", 
                              value=bool(cfg.get("qr_fallback_enabled", True)),
                              help="Uses api.qrserver.com when local decoding fails")
            
            submitted = st.form_submit_button("💾 Save Settings", type="primary", use_container_width=True)
        
        if submitted:
            cfg["user_agent"] = ua.strip() or USER_AGENT
            cfg["qr_fallback_enabled"] = bool(qr_fb)
            save_settings(cfg)
            st.success("✅ Settings saved successfully!")
    
    with tab2:
        st.markdown("### Profile Settings")
        st.markdown("Update your profile information:")
        
        with st.form("profile_update_form"):
            name = st.text_input("Full Name", value=user.get('name', ''))
            phone = st.text_input("Phone Number", value=user.get('phone', ''))
            address = st.text_input("Address", value=user.get('address', ''))
            
            st.markdown("**Your Roles**")
            current_roles = json.loads(user.get('roles', '[]'))
            role_cook = st.checkbox("🍳 Cook", value="COOK" in current_roles)
            role_driver = st.checkbox("🚗 Driver", value="DRIVER" in current_roles)
            role_hub = st.checkbox("🏢 Hub Manager", value="HUB" in current_roles)
            role_lighthouse = st.checkbox("🏠 Lighthouse", value="LIGHTHOUSE" in current_roles)
            
            update_profile = st.form_submit_button("💾 Update Profile", type="primary", use_container_width=True)
        
        if update_profile:
            roles = []
            if role_cook: roles.append("COOK")
            if role_driver: roles.append("DRIVER")
            if role_hub: roles.append("HUB")
            if role_lighthouse: roles.append("LIGHTHOUSE")
            
            if not roles:
                st.error("❌ Please select at least one role")
            else:
                updated_user = create_or_update_user(
                    name, user['email'], phone, roles, 
                    address, user.get('lat'), user.get('lon')
                )
                st.session_state["user"] = updated_user
                st.success("✅ Profile updated successfully!")
                st.rerun()
    
    with tab3:
        st.markdown("### Privacy & Data")
        
        st.markdown("**Your Data**")
        st.info("You can export all your data from the Profile page.")
        
        st.markdown("**Account Actions**")
        st.warning("⚠️ Danger Zone")
        
        with st.expander("🗑️ Delete My Account", expanded=False):
            st.markdown("""
            **Warning:** This action cannot be undone. All your data will be permanently deleted:
            - Your profile information
            - All dishes you've logged
            - Your trip history
            - Your notifications
            """)
            
            confirm_delete = st.text_input("Type 'DELETE' to confirm", key="confirm_delete")
            if st.button("Delete My Account Permanently", type="primary"):
                if confirm_delete == "DELETE":
                    # Delete user data
                    execute("DELETE FROM notifications WHERE user_id=?", (user["id"],))
                    execute("DELETE FROM dishes WHERE cook_id=?", (user["id"],))
                    execute("DELETE FROM trips WHERE driver_id=?", (user["id"],))
                    execute("DELETE FROM users WHERE id=?", (user["id"],))
                    st.session_state.clear()
                    st.success("Account deleted. Goodbye!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Please type 'DELETE' to confirm")

def admin_page():
    user = st.session_state.get("user")
    if not user:
        st.warning("⚠️ Please sign in to access this page.")
        if st.button("Go to Sign In"):
            goto("Sign In")
        return
    
    st.markdown("## 🔧 Admin Dashboard")
    st.caption("Platform management and analytics")
    
    st.divider()
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌱 Seed Default Data", use_container_width=True):
            ensure_seed_data()
            st.success("✅ Default hub and lighthouse created!")
    
    with col2:
        if st.button("🎭 Load Demo Data", use_container_width=True):
            res = seed_dummy_data()
            st.success(f"✅ Demo loaded: {res['users']} users, {res['dishes']} dishes, {res['trips']} trips")
            st.rerun()
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    st.divider()
    
    # Platform statistics
    st.markdown("### 📊 Platform Analytics")
    
    total_users = fetch_one("SELECT COUNT(*) AS c FROM users")["c"]
    total_dishes = fetch_one("SELECT COUNT(*) AS c FROM dishes")["c"]
    total_portions = fetch_one("SELECT COALESCE(SUM(portions),0) AS s FROM dishes")["s"]
    active_trips = fetch_one("SELECT COUNT(*) AS c FROM trips WHERE status='active'")["c"]
    distributed = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE status='distributed'")["c"]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👥 Total Users", total_users)
    col2.metric("🍽️ Total Dishes", total_dishes)
    col3.metric("🥘 Total Portions", total_portions)
    col4.metric("🚗 Active Trips", active_trips)
    col5.metric("✅ Distributed", distributed)
    
    st.divider()
    
    # Detailed views
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Hubs", "🏠 Lighthouses", "📊 Reports", "📥 Export"])
    
    with tab1:
        st.markdown("### Hub Management")
        hubs = fetch_all("SELECT * FROM hubs")
        if hubs:
            df_hubs = pd.DataFrame(hubs)
            st.dataframe(df_hubs, use_container_width=True)
        else:
            st.info("No hubs configured yet")
        
        with st.expander("➕ Add New Hub"):
            with st.form("add_hub_form"):
                hub_name = st.text_input("Hub Name")
                hub_address = st.text_input("Address")
                col1, col2 = st.columns(2)
                hub_lat = col1.number_input("Latitude", format="%.6f", value=-33.9249)
                hub_lon = col2.number_input("Longitude", format="%.6f", value=18.4241)
                
                if st.form_submit_button("Add Hub", type="primary"):
                    if hub_name:
                        hid = uuid()
                        execute("INSERT INTO hubs (id, name, address, lat, lon) VALUES (?,?,?,?,?)",
                               (hid, hub_name, hub_address, hub_lat, hub_lon))
                        st.success(f"✅ Hub '{hub_name}' added!")
                        st.rerun()
    
    with tab2:
        st.markdown("### Lighthouse Management")
        lighthouses = fetch_all("SELECT * FROM lighthouses")
        if lighthouses:
            df_lh = pd.DataFrame(lighthouses)
            st.dataframe(df_lh, use_container_width=True)
        else:
            st.info("No lighthouses configured yet")
        
        with st.expander("➕ Add New Lighthouse"):
            with st.form("add_lighthouse_form"):
                lh_name = st.text_input("Lighthouse Name")
                lh_address = st.text_input("Address")
                col1, col2 = st.columns(2)
                lh_lat = col1.number_input("Latitude", format="%.6f", value=-33.93)
                lh_lon = col2.number_input("Longitude", format="%.6f", value=18.42)
                
                if st.form_submit_button("Add Lighthouse", type="primary"):
                    if lh_name:
                        lid = uuid()
                        execute("INSERT INTO lighthouses (id, name, address, lat, lon) VALUES (?,?,?,?,?)",
                               (lid, lh_name, lh_address, lh_lat, lh_lon))
                        st.success(f"✅ Lighthouse '{lh_name}' added!")
                        st.rerun()
    
    with tab3:
        st.markdown("### Platform Reports")
        
        # Status distribution
        st.markdown("#### Dish Status Distribution")
        status_counts = {}
        for status in STATUSES:
            count = fetch_one("SELECT COUNT(*) AS c FROM dishes WHERE status=?", (status,))["c"]
            status_counts[status.replace('_', ' ').title()] = count
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if any(status_counts.values()):
                chart_data = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
                st.bar_chart(chart_data.set_index('Status'))
        with col2:
            for status, count in status_counts.items():
                st.metric(status, count)
        
        st.markdown("#### User Role Distribution")
        users = fetch_all("SELECT roles FROM users")
        role_counts = {"COOK": 0, "DRIVER": 0, "HUB": 0, "LIGHTHOUSE": 0}
        for u in users:
            roles = json.loads(u.get('roles', '[]'))
            for r in roles:
                if r in role_counts:
                    role_counts[r] += 1
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🍳 Cooks", role_counts["COOK"])
        col2.metric("🚗 Drivers", role_counts["DRIVER"])
        col3.metric("🏢 Hub Managers", role_counts["HUB"])
        col4.metric("🏠 Lighthouses", role_counts["LIGHTHOUSE"])
    
    with tab4:
        st.markdown("### Export Data")
        st.caption("Download platform data for analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            all_dishes = fetch_all("SELECT * FROM dishes ORDER BY prepared_at DESC")
            if all_dishes:
                df_all_d = pd.DataFrame(all_dishes)
                csv_all_d = df_all_d.to_csv(index=False).encode("utf-8")
                st.download_button("📄 Download All Dishes", csv_all_d, 
                                 file_name="all_dishes.csv", mime="text/csv", use_container_width=True)
            
            all_users = fetch_all("SELECT * FROM users ORDER BY created_at DESC")
            if all_users:
                df_users = pd.DataFrame(all_users)
                csv_users = df_users.to_csv(index=False).encode("utf-8")
                st.download_button("👥 Download All Users", csv_users, 
                                 file_name="all_users.csv", mime="text/csv", use_container_width=True)
        
        with col2:
            all_trips = fetch_all("SELECT * FROM trips ORDER BY started_at DESC")
            if all_trips:
                df_all_t = pd.DataFrame(all_trips)
                csv_all_t = df_all_t.to_csv(index=False).encode("utf-8")
                st.download_button("🚗 Download All Trips", csv_all_t, 
                                 file_name="all_trips.csv", mime="text/csv", use_container_width=True)
            
            all_notifications = fetch_all("SELECT * FROM notifications ORDER BY created_at DESC")
            if all_notifications:
                df_notif = pd.DataFrame(all_notifications)
                csv_notif = df_notif.to_csv(index=False).encode("utf-8")
                st.download_button("🔔 Download Notifications", csv_notif, 
                                 file_name="notifications.csv", mime="text/csv", use_container_width=True)

# ---------------------------
# App entrypoint
# ---------------------------
def main():
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🍲",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    inject_custom_css()
    init_db()
    
    if "page" not in st.session_state:
        st.session_state["page"] = "Home"
    
    header()
    
    # Enforce application flow
    user = st.session_state.get("user")
    page = st.session_state.get("page", "Home")
    
    if user and page in ("Sign Up", "Sign In"):
        st.session_state["page"] = "Home"
        st.rerun()
    
    if not user and page in {"Cook", "Driver", "Hub", "Lighthouse", "Profile", "Settings", "Admin"}:
        st.session_state["page"] = "Sign In"
        st.rerun()
    
    # Route to pages
    page_map = {
        "Home": home_page,
        "Sign Up": sign_up_page,
        "Sign In": sign_in_page,
        "Cook": cook_page,
        "Driver": driver_page,
        "Hub": hub_page,
        "Lighthouse": lighthouse_page,
        "Profile": profile_page,
        "Safety Guide": safety_guide_page,
        "Settings": settings_page,
        "Admin": admin_page
    }
    
    page_func = page_map.get(page, home_page)
    page_func()
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption(f"© 2025 {APP_NAME} - {APP_TAGLINE}")
    with col2:
        st.caption("Made with ❤️ for the community")
    with col3:
        st.caption("v1.0.0")

if __name__ == "__main__":
    main()