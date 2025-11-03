import { useEffect, useMemo, useState } from "react";
import { MapPin, QrCode, Scan, Users, Gift, Truck, Bell, Plus, CheckCircle2, Trophy, Clock, Loader2, Search, Settings, UserPlus, Phone, Mail, Home, X } from "lucide-react";

// Brand theme (from marketing palette)
const BRAND = { primary: "#7A4E2B", primaryDark: "#6d4527", sand: "#EFE4D8", sand2: "#F7EFE7", border: "#D7C5B4", ink: "#3A2A1A" };

// Inline logo mark (fish + loaves) inspired by provided assets
function LogoMark({ className = "h-6 w-auto" }) {
  return (
    <svg className={className} viewBox="0 0 240 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* three loaves */}
      <g stroke={BRAND.ink} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M25 32c6 0 11-7 11-14S31 4 25 4 14 11 14 18s5 14 11 14z" />
        <path d="M35 18c-4 2-8 2-12 0" />
      </g>
      <g stroke={BRAND.ink} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M85 32c6 0 11-7 11-14S91 4 85 4 74 11 74 18s5 14 11 14z" />
        <path d="M95 18c-4 2-8 2-12 0" />
      </g>
      <g stroke={BRAND.ink} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M145 32c6 0 11-7 11-14s-5-14-11-14-11 7-11 14 5 14 11 14z" />
        <path d="M155 18c-4 2-8 2-12 0" />
      </g>
      {/* fish */}
      <g stroke={BRAND.ink} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M205 6c8 5 8 19 0 26" />
        <path d="M205 32c-9-4-19-4-28 0 4-8 4-18 0-26 9 4 19 4 28 0z" />
      </g>
    </svg>
  );
}

// --- Simple in-file "DB" wrapper around localStorage ---
const STORAGE_KEY = "jom_db_v1";
const MIN_COLLECTION_QTY = 5; // meals

function loadDB() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) {
    console.error("Failed to load DB", e);
    return null;
  }
}

function saveDB(db) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  } catch (e) {
    console.error("Failed to save DB", e);
  }
}

function uid(prefix = "id") {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}_${Date.now().toString(36)}`;
}

function nowISO() {
  return new Date().toISOString();
}

// Haversine distance in KM
function haversineKm(a, b) {
  const toRad = (d) => (d * Math.PI) / 180;
  const R = 6371; // km
  const dLat = toRad(b.lat - a.lat);
  const dLon = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  return R * c;
}

// Seed demo lighthouses around South Africa
const SEED_LIGHTHOUSES = [
  { id: "lh_cpt", name: "Cape Town Lighthouse", lat: -33.9249, lng: 18.4241, radiusKm: 15, dropPoints: ["Sea Point", "Claremont"] },
  { id: "lh_jhb", name: "Johannesburg Lighthouse", lat: -26.2041, lng: 28.0473, radiusKm: 20, dropPoints: ["Rosebank", "Sandton"] },
  { id: "lh_dbn", name: "Durban Lighthouse", lat: -29.8587, lng: 31.0218, radiusKm: 15, dropPoints: ["Umhlanga", "Glenwood"] },
  { id: "lh_pta", name: "Pretoria Lighthouse", lat: -25.7479, lng: 28.2293, radiusKm: 20, dropPoints: ["Hatfield", "Menlyn"] },
];

// --- Types (informal) ---
// Contributor: { id, name, phone?, email?, address?, lat?, lng?, createdAt, points, mealsContributed }
// Meal: { id(qr), contributorId, preparedDate, description, mealType: 'beef'|'pork'|'fish'|'vegetarian', contains: {treeNuts, eggs, peanuts, shellfish, dairy, wheat, soy}, method: 'dropoff'|'collect', lighthouseId, status: 'logged'|'at_lighthouse'|'distributed', recipientName?, distributedAt? }

function useDB() {
  const [db, setDb] = useState(() => {
    const existing = loadDB();
    if (existing) return existing;
    return {
      contributors: [],
      lighthouses: SEED_LIGHTHOUSES,
      meals: [],
      notifications: [],
    };
  });

  useEffect(() => {
    saveDB(db);
  }, [db]);

  const api = {
    reset: () => setDb({ contributors: [], lighthouses: SEED_LIGHTHOUSES, meals: [], notifications: [] }),
    addContributor: (c) => setDb((d) => ({ ...d, contributors: [...d.contributors, c] })),
    updateContributor: (id, patch) => setDb((d) => ({
      ...d,
      contributors: d.contributors.map((c) => (c.id === id ? { ...c, ...patch } : c)),
    })),
    upsertMeal: (meal) => setDb((d) => {
      const idx = d.meals.findIndex((m) => m.id === meal.id);
      if (idx >= 0) {
        const meals = [...d.meals];
        meals[idx] = { ...meals[idx], ...meal };
        return { ...d, meals };
      }
      return { ...d, meals: [...d.meals, meal] };
    }),
    addNotification: (n) => setDb((d) => ({ ...d, notifications: [n, ...d.notifications].slice(0, 100) })),
  };

  return [db, api];
}

function Header({ onLogout, onOpenSettings }) {
  return (
    <header className="sticky top-0 z-20 bg-[#EFE4D8]/80 backdrop-blur border-b border-[#D7C5B4]">
      <div className="mx-auto max-w-screen-sm px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <LogoMark className="h-6" />
          <h1 className="tracking-[0.3em] text-base sm:text-2xl font-black text-[#3A2A1A]">JUST ONE MORE</h1>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onOpenSettings} className="p-2 rounded-xl hover:bg-[#F7EFE7] active:scale-95 transition">
            <Settings className="h-5 w-5" />
          </button>
          <button onClick={onLogout} className="px-3 py-1.5 text-sm rounded-xl bg-[#7A4E2B] text-white hover:bg-[#6d4527] active:scale-[0.98]">Log out</button>
        </div>
      </div>
    </header>
  );
}

function Pill({ children }) {
  return <span className="rounded-full px-2 py-0.5 text-xs bg-[#F7EFE7] border border-[#D7C5B4]">{children}</span>;
}

function Section({ title, icon: Icon, children, actions }) {
  return (
    <section className="bg-white rounded-2xl shadow-sm border border-[#D7C5B4] p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {Icon ? <Icon className="h-5 w-5" /> : null}
          <h2 className="text-base font-semibold">{title}</h2>
        </div>
        <div className="flex items-center gap-2">{actions}</div>
      </div>
      {children}
    </section>
  );
}

function Empty({ icon: Icon, title, subtitle, action }) {
  return (
    <div className="flex flex-col items-center text-center p-6">
      {Icon ? <Icon className="h-10 w-10 mb-2" /> : null}
      <p className="font-medium">{title}</p>
      {subtitle ? <p className="text-sm text-neutral-500 mt-1">{subtitle}</p> : null}
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

function requestPushPermission() {
  if (!("Notification" in window)) return false;
  if (Notification.permission === "granted") return true;
  if (Notification.permission !== "denied") {
    Notification.requestPermission();
  }
  return Notification.permission === "granted";
}

function sendPush(title, body) {
  try {
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(title, { body });
    }
  } catch (e) {
    // ignore
  }
}

function useGeo() {
  const [coords, setCoords] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const getLocation = () => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported");
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLoading(false);
      },
      (err) => {
        setError(err.message || "Failed to get location");
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  };

  return { coords, loading, error, getLocation };
}

// helpers used by validation + tests
function hasAnyTrue(obj) {
  return Object.values(obj || {}).some(Boolean);
}

// NEW: bulk id generator used by the bulk upload flow
function generateBulkIds(base, quantity) {
  const trimmed = String(base || "").trim();
  if (!trimmed) return [];
  const q = Math.max(1, Number(quantity) || 1);
  if (q === 1) return [trimmed];
  return Array.from({ length: q }, (_, i) => `${trimmed}-${String(i + 1).padStart(2, "0")}`);
}

// lightweight dev tests for helpers
(function devTests() {
  try {
    // existing tests (do not modify)
    console.assert(hasAnyTrue({}) === false, "hasAnyTrue empty should be false");
    console.assert(hasAnyTrue({ a: false, b: true }) === true, "hasAnyTrue should detect true value");

    // NEW tests for generateBulkIds
    const one = generateBulkIds("ABC", 1);
    console.assert(Array.isArray(one) && one.length === 1 && one[0] === "ABC", "bulkIds (1) failed");

    const three = generateBulkIds("ABC", 3);
    console.assert(
      Array.isArray(three) &&
        three.length === 3 &&
        three[0] === "ABC-01" &&
        three[1] === "ABC-02" &&
        three[2] === "ABC-03",
      "bulkIds (3) failed"
    );

    const emptyBase = generateBulkIds("   ", 2);
    console.assert(Array.isArray(emptyBase) && emptyBase.length === 0, "bulkIds empty base should be []");

    const pad = generateBulkIds("X", 10);
    console.assert(pad[9] === "X-10", "bulkIds pad to two digits up to 10");
  } catch (e) {
    // do not crash UI on failed test
  }
})();

function Onboarding({ onComplete }) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const { coords, loading, error, getLocation } = useGeo();

  const canContinue = name.trim().length >= 2;

  return (
    <div className="mx-auto max-w-screen-sm p-4">
      <div className="flex flex-col items-center gap-2 pt-8">
        <LogoMark className="h-10 w-auto" />
        <h1 className="text-2xl font-bold">Welcome to Just One More</h1>
        <p className="text-neutral-600 text-center">Pack an extra meal, make a big difference. Create your contributor profile in seconds.</p>
      </div>

      <div className="mt-6 space-y-4">
        <Section title="Your details" icon={UserPlus}>
          <div className="space-y-3">
            <label className="flex items-center gap-3 border border-[#D7C5B4] rounded-xl p-3">
              <Users className="h-4 w-4 text-neutral-500" />
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" className="w-full outline-none" />
            </label>
            <label className="flex items-center gap-3 border border-[#D7C5B4] rounded-xl p-3">
              <Phone className="h-4 w-4 text-neutral-500" />
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Mobile (optional)" className="w-full outline-none" />
            </label>
            <label className="flex items-center gap-3 border border-[#D7C5B4] rounded-xl p-3">
              <Mail className="h-4 w-4 text-neutral-500" />
              <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email (optional)" type="email" className="w-full outline-none" />
            </label>
            <label className="flex items-center gap-3 border border-[#D7C5B4] rounded-xl p-3">
              <Home className="h-4 w-4 text-neutral-500" />
              <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Suburb / Address (optional)" className="w-full outline-none" />
            </label>
          </div>
        </Section>

        <Section title="Location (for nearest Lighthouse)" icon={MapPin}>
          <div className="flex items-center gap-3">
            <button onClick={getLocation} disabled={loading} className="px-3 py-2 rounded-xl bg-[#7A4E2B] text-white hover:bg-[#6d4527] active:scale-[0.98] flex items-center gap-2">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <MapPin className="h-4 w-4" />} Use my current location
            </button>
            {coords ? <Pill>{coords.lat.toFixed(3)}, {coords.lng.toFixed(3)}</Pill> : null}
          </div>
          {error ? <p className="text-sm text-red-600 mt-2">{error}</p> : null}
        </Section>

        <button
          disabled={!canContinue}
          onClick={() => onComplete({ id: uid("ctr"), name, phone, email, address, lat: coords?.lat, lng: coords?.lng, createdAt: nowISO(), points: 0, mealsContributed: 0 })}
          className="w-full py-3 rounded-2xl bg-[#7A4E2B] text-white text-base font-medium hover:bg-[#6d4527] active:scale-[0.99] disabled:opacity-50"
        >
          Create my profile
        </button>
      </div>
    </div>
  );
}

function LighthouseFinder({ lighthouses, userCoords, onSelect }) {
  const enriched = useMemo(() => {
    return lighthouses
      .map((lh) => {
        let dist = null;
        if (userCoords) dist = haversineKm(userCoords, { lat: lh.lat, lng: lh.lng });
        return { ...lh, dist };
      })
      .sort((a, b) => (a.dist ?? Infinity) - (b.dist ?? Infinity));
  }, [lighthouses, userCoords]);

  return (
    <Section title="Nearest Lighthouse" icon={MapPin}>
      {!userCoords && <p className="text-sm text-neutral-600 mb-3">Allow location in onboarding to automatically sort by distance.</p>}
      <div className="space-y-2">
        {enriched.map((lh) => (
          <button key={lh.id} onClick={() => onSelect(lh)} className="w-full text-left p-3 rounded-xl border border-[#D7C5B4] hover:bg-[#F7EFE7] flex items-center justify-between">
            <div>
              <p className="font-medium">{lh.name}</p>
              <p className="text-xs text-neutral-500">Service radius ~{lh.radiusKm} km{lh.dropPoints?.length ? ` • Drop-off: ${lh.dropPoints.join(", ")}` : ""}</p>
            </div>
            <div className="text-right">{lh.dist != null ? <p className="text-sm">{lh.dist.toFixed(1)} km</p> : <p className="text-sm">—</p>}</div>
          </button>
        ))}
      </div>
    </Section>
  );
}

function QRInput({ value, onChange, onScan }) {
  const [open, setOpen] = useState(false);
  const [temp, setTemp] = useState("");
  return (
    <div className="flex items-center gap-2">
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Enter / scan container QR" className="flex-1 border border-[#D7C5B4] rounded-xl p-3 outline-none" />
      <button onClick={() => setOpen(true)} className="p-3 rounded-xl border border-[#D7C5B4] hover:bg-[#F7EFE7]">
        <Scan className="h-4 w-4" />
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-sm rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <QrCode className="h-5 w-5" />
                <p className="font-medium">Scan QR (demo)</p>
              </div>
              <button onClick={() => setOpen(false)} className="p-2 hover:bg-neutral-100 rounded-xl">
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-sm text-neutral-600">
              For the prototype, type or paste a QR/Container ID. (Camera scanning can be wired to a library like <code>html5-qrcode</code>.)
            </p>
            <input value={temp} onChange={(e) => setTemp(e.target.value)} placeholder="QR / Container ID" className="w-full border border-[#D7C5B4] rounded-xl p-3 outline-none" />
            <button
              onClick={() => {
                if (!temp.trim()) return;
                onChange(temp.trim());
                onScan?.(temp.trim());
                setOpen(false);
                setTemp("");
              }}
              className="w-full py-3 rounded-xl bg-[#7A4E2B] text-white hover:bg-[#6d4527]"
            >
              Use this code
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ContributeFlow({ profile, db, api }) {
  const [selectedLH, setSelectedLH] = useState(null);
  const [qr, setQr] = useState("");
  const [date, setDate] = useState("");
  const [description, setDescription] = useState("chicken soup");
  const [quantity, setQuantity] = useState(1);

  // Meal type radio + allergens (no contradictory choices)
  const [mealType, setMealType] = useState("vegetarian"); // 'beef' | 'pork' | 'fish' | 'vegetarian'
  const [contains, setContains] = useState({
    treeNuts: false,
    eggs: false,
    peanuts: false,
    shellfish: false,
    dairy: false,
    wheat: false,
    soy: false,
  });

  const [method, setMethod] = useState("dropoff");
  const [confirmIds, setConfirmIds] = useState([]);

  const myCoords = profile?.lat && profile?.lng ? { lat: profile.lat, lng: profile.lng } : null;

  // Auto-select nearest lighthouse when user has coords
  useEffect(() => {
    if (!selectedLH && myCoords && db.lighthouses?.length) {
      const nearest = [...db.lighthouses].sort(
        (a, b) => haversineKm(myCoords, { lat: a.lat, lng: a.lng }) - haversineKm(myCoords, { lat: b.lat, lng: b.lng })
      )[0];
      if (nearest) setSelectedLH(nearest);
    }
  }, [selectedLH, myCoords, db.lighthouses]);

  const myMealsAwaiting = useMemo(
    () => db.meals.filter((m) => m.contributorId === profile.id && m.status !== "distributed"),
    [db.meals, profile.id]
  );

  const handleSubmit = () => {
    const ids = generateBulkIds(qr, quantity);
    if (ids.length === 0) return; // require a base id

    ids.forEach((id) => {
      const meal = {
        id,
        contributorId: profile.id,
        preparedDate: date,
        description,
        mealType,
        contains,
        method,
        lighthouseId: selectedLH.id,
        status: "logged",
      };
      api.upsertMeal(meal);
    });

    setConfirmIds(ids);
    setQr("");
    setDate("");
    setDescription("chicken soup");
    setMealType("vegetarian");
    setContains({ treeNuts: false, eggs: false, peanuts: false, shellfish: false, dairy: false, wheat: false, soy: false });
    setQuantity(1);
  };

  const canSubmit = qr && date && selectedLH; // allergens optional now

  return (
    <div className="space-y-4">
      <LighthouseFinder lighthouses={db.lighthouses} userCoords={myCoords} onSelect={setSelectedLH} />

      <Section title="Log a meal" icon={QrCode} actions={selectedLH ? <Pill>{selectedLH.name}</Pill> : null}>
        <div className="space-y-3">
          <QRInput value={qr} onChange={setQr} />
          <div className="grid grid-cols-2 gap-2">
            <label className="border border-[#D7C5B4] rounded-xl p-3 text-sm flex items-center gap-2">
              <Clock className="h-4 w-4 text-neutral-500" />
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="outline-none" />
            </label>
            <label className="border border-[#D7C5B4] rounded-xl p-3 text-sm flex items-center gap-2">
              <Truck className="h-4 w-4 text-neutral-500" />
              <select value={method} onChange={(e) => setMethod(e.target.value)} className="outline-none">
                <option value="dropoff">I'll drop it off</option>
                <option value="collect">Please collect (min {MIN_COLLECTION_QTY})</option>
              </select>
            </label>
            {/* Quantity dropdown for bulk upload */}
            <label className="border border-[#D7C5B4] rounded-xl p-3 text-sm flex items-center gap-2 col-span-2 sm:col-span-1">
              <Plus className="h-4 w-4 text-neutral-500" />
              <select value={quantity} onChange={(e) => setQuantity(parseInt(e.target.value))} className="outline-none">
                {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    {n} {n === 1 ? "meal" : "meals"}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="space-y-2">
            <label className="border border-[#D7C5B4] rounded-xl p-3 text-sm flex items-center gap-2">
              <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (e.g. 'chicken soup')" className="w-full outline-none" />
            </label>

            {/* Meal type radios */}
            <p className="text-sm font-medium">Meal type</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { key: "vegetarian", label: "Vegetarian" },
                { key: "beef", label: "Beef" },
                { key: "pork", label: "Pork" },
                { key: "fish", label: "Fish" },
              ].map((opt) => (
                <label key={opt.key} className={`border rounded-xl p-3 text-sm flex items-center gap-2 ${mealType === opt.key ? "border-[#7A4E2B] bg-[#F7EFE7]" : "border-[#D7C5B4]"}`}>
                  <input type="radio" name="mealType" checked={mealType === opt.key} onChange={() => setMealType(opt.key)} />
                  {opt.label}
                </label>
              ))}
            </div>

            {/* Allergens checkboxes */}
            <p className="text-sm font-medium mt-2">Allergens</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { key: "eggs", label: "Eggs" },
                { key: "treeNuts", label: "Tree nuts" },
                { key: "peanuts", label: "Peanuts" },
                { key: "shellfish", label: "Shellfish" },
                { key: "dairy", label: "Dairy" },
                { key: "wheat", label: "Wheat" },
                { key: "soy", label: "Soy" },
              ].map((opt) => (
                <label key={opt.key} className={`border rounded-xl p-3 text-sm flex items-center gap-2 ${contains[opt.key] ? "border-[#7A4E2B] bg-[#F7EFE7]" : "border-[#D7C5B4]"}`}>
                  <input type="checkbox" checked={!!contains[opt.key]} onChange={(e) => setContains((t) => ({ ...t, [opt.key]: e.target.checked }))} />
                  {opt.label}
                </label>
              ))}
            </div>
          </div>

          <button disabled={!canSubmit} onClick={handleSubmit} className="w-full py-3 rounded-2xl bg-[#7A4E2B] text-white hover:bg-[#6d4527] disabled:opacity-50">
            Save meal
          </button>

          {confirmIds.length > 0 && (
            <div className="mt-2 p-3 rounded-xl bg-green-50 border border-green-200 text-sm flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              {confirmIds.length === 1 ? (
                <>
                  Meal <span className="font-mono">{confirmIds[0]}</span> saved.
                </>
              ) : (
                <>
                  {confirmIds.length} meals saved. First code: <span className="font-mono">{confirmIds[0]}</span>
                </>
              )}
              {" "}
              {method === "collect"
                ? `We'll notify you once a pickup is scheduled with ${selectedLH?.name}.`
                : `Drop off at ${selectedLH?.name} or nearby point.`}
            </div>
          )}
        </div>
      </Section>

      {myMealsAwaiting.length > 0 && (
        <Section title="Your pending meals" icon={Gift}>
          <ul className="divide-y">
            {myMealsAwaiting.map((m) => (
              <li key={m.id} className="py-3 flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    Container: <span className="font-mono">{m.id}</span>
                  </p>
                  <p className="text-xs text-neutral-500">
                    {m.preparedDate} • {m.method === "collect" ? "Collection requested" : "Drop-off"}
                  </p>
                </div>
                <Pill>{db.lighthouses.find((l) => l.id === m.lighthouseId)?.name ?? "—"}</Pill>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Need help?" icon={Bell}>
        <p className="text-sm text-neutral-600">Questions about drop-off points, collection minimums, or contents? Reach out to your Lighthouse keeper after logging a meal.</p>
      </Section>
    </div>
  );
}

function KeeperView({ db, api }) {
  const [tab, setTab] = useState("inbound");
  const [qr, setQr] = useState("");
  const [recipient, setRecipient] = useState("");
  const [filter, setFilter] = useState("");

  const inbound = useMemo(() => db.meals.filter((m) => m.status === "logged" || m.status === "at_lighthouse"), [db.meals]);
  const toShow = useMemo(() => inbound.filter((m) => !filter || m.id.toLowerCase().includes(filter.toLowerCase())), [inbound, filter]);

  const handleReceive = (id) => {
    api.upsertMeal({ id, status: "at_lighthouse" });
  };

  const handleDistribute = (id) => {
    const meal = db.meals.find((m) => m.id === id);
    if (!meal) return;
    api.upsertMeal({ id, status: "distributed", distributedAt: nowISO(), recipientName: recipient || "—" });
    // Award points to contributor
    const ctr = db.contributors.find((c) => c.id === meal.contributorId);
    if (ctr) {
      const newPoints = (ctr.points || 0) + 10; // 10 pts per meal
      const newMeals = (ctr.mealsContributed || 0) + 1;
      // Simple badge logic
      const milestone = [1, 5, 10, 25, 50].find((m) => newMeals === m);
      api.updateContributor(ctr.id, { points: newPoints, mealsContributed: newMeals });
      const thanks = `Your meal ${id} has been delivered. Thank you!`;
      api.addNotification({ id: uid("ntf"), ts: nowISO(), contributorId: ctr.id, message: thanks });
      sendPush("Just One More", thanks);
      if (milestone) {
        const msg = `🎉 Milestone: ${milestone} meal${milestone > 1 ? "s" : ""} delivered!`;
        api.addNotification({ id: uid("ntf"), ts: nowISO(), contributorId: ctr.id, message: msg });
      }
    }
    setQr("");
    setRecipient("");
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-2">
        {[
          { key: "inbound", label: "Incoming" },
          { key: "handover", label: "Scan out" },
          { key: "search", label: "Search" },
        ].map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} className={`py-2 rounded-xl border ${tab === t.key ? "border-[#7A4E2B] bg-[#F7EFE7]" : "border-[#D7C5B4]"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "inbound" && (
        <Section title="Meals at / en route to Lighthouse" icon={Truck}>
          {inbound.length === 0 ? (
            <Empty icon={Gift} title="Nothing here yet" subtitle="Meals logged by contributors will appear here to receive and manage." />
          ) : (
            <ul className="divide-y">
              {inbound.map((m) => (
                <li key={m.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      Container <span className="font-mono">{m.id}</span>{" "}
                      <span className="text-xs text-neutral-500">• {m.preparedDate}</span>
                    </p>
                    <p className="text-xs text-neutral-500 capitalize">
                      {m.method} • {db.contributors.find((c) => c.id === m.contributorId)?.name || "Contributor"}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {m.status !== "at_lighthouse" && (
                      <button onClick={() => handleReceive(m.id)} className="px-3 py-1.5 rounded-xl border border-[#D7C5B4] hover:bg-[#F7EFE7]">
                        Mark received
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>
      )}

      {tab === "handover" && (
        <Section title="Scan out to recipient" icon={Scan}>
          <div className="space-y-3">
            <QRInput value={qr} onChange={setQr} />
            <label className="border border-[#D7C5B4] rounded-xl p-3 text-sm flex items-center gap-2">
              <Users className="h-4 w-4 text-neutral-500" />
              <input value={recipient} onChange={(e) => setRecipient(e.target.value)} placeholder="Recipient name (optional)" className="outline-none w-full" />
            </label>
            <button disabled={!qr} onClick={() => handleDistribute(qr)} className="w-full py-3 rounded-2xl bg-[#7A4E2B] text-white hover:bg-[#6d4527] disabled:opacity-50">
              Confirm handover
            </button>
            <p className="text-xs text-neutral-500">Contributor will automatically get a thank-you notification.</p>
          </div>
        </Section>
      )}

      {tab === "search" && (
        <Section title="Find a container" icon={Search}>
          <div className="space-y-3">
            <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Search by container ID" className="w-full border border-[#D7C5B4] rounded-xl p-3 outline-none" />
            <ul className="divide-y">
              {toShow.map((m) => (
                <li key={m.id} className="py-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{m.id}</p>
                      <p className="text-xs text-neutral-500">
                        {m.status} • {m.preparedDate}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {m.status !== "at_lighthouse" && (
                        <button onClick={() => handleReceive(m.id)} className="px-3 py-1.5 rounded-xl border border-[#D7C5B4] hover:bg-[#F7EFE7]">
                          Mark received
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </Section>
      )}
    </div>
  );
}

function Impact({ db, me }) {
  const myMeals = db.meals.filter((m) => m.contributorId === me.id);
  const delivered = myMeals.filter((m) => m.status === "distributed").length;
  const pending = myMeals.length - delivered;

  const topContributors = useMemo(() => {
    return [...db.contributors].sort((a, b) => (b.points || 0) - (a.points || 0)).slice(0, 5);
  }, [db.contributors]);

  const badges = useMemo(() => {
    const count = delivered;
    const earned = [];
    if (count >= 1) earned.push({ title: "First Meal", desc: "Your first contribution!" });
    if (count >= 5) earned.push({ title: "Helping Hand", desc: "5 meals delivered." });
    if (count >= 10) earned.push({ title: "Community Hero", desc: "10 meals delivered." });
    if (count >= 25) earned.push({ title: "Lighthouse Star", desc: "25 meals delivered." });
    if (count >= 50) earned.push({ title: "Champion", desc: "50 meals delivered." });
    return earned;
  }, [delivered]);

  return (
    <div className="space-y-4">
      <Section title="Your impact" icon={Trophy}>
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-2xl border border-[#D7C5B4] p-3 text-center">
            <p className="text-2xl font-bold">{delivered}</p>
            <p className="text-xs text-neutral-500">Meals delivered</p>
          </div>
          <div className="rounded-2xl border border-[#D7C5B4] p-3 text-center">
            <p className="text-2xl font-bold">{pending}</p>
            <p className="text-xs text-neutral-500">Awaiting</p>
          </div>
          <div className="rounded-2xl border border-[#D7C5B4] p-3 text-center">
            <p className="text-2xl font-bold">{me.points || 0}</p>
            <p className="text-xs text-neutral-500">Points</p>
          </div>
        </div>
      </Section>

      <Section title="Badges" icon={CheckCircle2}>
        {badges.length === 0 ? (
          <Empty icon={CheckCircle2} title="No badges yet" subtitle="Deliver meals to unlock achievement badges." />
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {badges.map((b, i) => (
              <div key={i} className="rounded-2xl border border-[#D7C5B4] p-3">
                <p className="font-medium">{b.title}</p>
                <p className="text-xs text-neutral-500">{b.desc}</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Leaderboard" icon={Users}>
        {topContributors.length === 0 ? (
          <Empty icon={Users} title="No contributors yet" />
        ) : (
          <ol className="space-y-2">
            {topContributors.map((c, idx) => (
              <li key={c.id} className="flex items-center justify-between rounded-2xl border border-[#D7C5B4] p-3">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full border border-[#D7C5B4] grid place-items-center text-xs">{idx + 1}</span>
                  <div>
                    <p className="font-medium">{c.name}</p>
                    <p className="text-xs text-neutral-500">{c.mealsContributed || 0} meals</p>
                  </div>
                </div>
                <Pill>{c.points || 0} pts</Pill>
              </li>
            ))}
          </ol>
        )}
      </Section>

      <Section title="Notifications" icon={Bell}>
        <ul className="divide-y">
          {db.notifications.filter((n) => n.contributorId === me.id).map((n) => (
            <li key={n.id} className="py-3 text-sm">
              <p>{n.message}</p>
              <p className="text-xs text-neutral-500 mt-0.5">{new Date(n.ts).toLocaleString()}</p>
            </li>
          ))}
          {db.notifications.filter((n) => n.contributorId === me.id).length === 0 && <Empty icon={Bell} title="No notifications yet" />}
        </ul>
      </Section>
    </div>
  );
}

export default function App() {
  const [db, api] = useDB();
  const [me, setMe] = useState(null);
  const [activeTab, setActiveTab] = useState("contribute");
  const [isKeeperMode, setKeeperMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Restore last session
  useEffect(() => {
    const lastId = sessionStorage.getItem("jom_last_contributor");
    if (lastId) {
      const ctr = db.contributors.find((c) => c.id === lastId);
      if (ctr) setMe(ctr);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (me) sessionStorage.setItem("jom_last_contributor", me.id);
  }, [me]);

  useEffect(() => {
    requestPushPermission();
  }, []);

  const handleOnboard = (ctr) => {
    api.addContributor(ctr);
    setMe(ctr);
  };

  const logout = () => {
    setMe(null);
    sessionStorage.removeItem("jom_last_contributor");
  };

  if (!me) {
    return <Onboarding onComplete={handleOnboard} />;
  }

  return (
    <div className="min-h-dvh bg-[#EFE4D8] text-[#3A2A1A]">
      <Header onLogout={logout} onOpenSettings={() => setShowSettings(true)} />

      <main className="mx-auto max-w-screen-sm p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <p className="text-sm text-neutral-500">Logged in as</p>
            <p className="font-medium">{me.name}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm">Keeper mode</span>
            <button
              onClick={() => setKeeperMode((v) => !v)}
              className={`w-12 h-7 rounded-full border relative transition ${isKeeperMode ? "bg-[#7A4E2B] border-[#7A4E2B]" : "bg-white border-neutral-300"}`}
            >
              <span className={`absolute top-0.5 ${isKeeperMode ? "left-6" : "left-1"} w-6 h-6 rounded-full bg-white shadow`} />
            </button>
          </div>
        </div>

        {!isKeeperMode ? (
          <>
            <nav className="grid grid-cols-3 gap-2">
              {[
                { key: "contribute", label: "Contribute" },
                { key: "impact", label: "My Impact" },
                { key: "lighthouses", label: "Lighthouses" },
              ].map((t) => (
                <button key={t.key} onClick={() => setActiveTab(t.key)} className={`py-2 rounded-xl border ${activeTab === t.key ? "border-[#7A4E2B] bg-[#F7EFE7]" : "border-[#D7C5B4]"}`}>
                  {t.label}
                </button>
              ))}
            </nav>

            {activeTab === "contribute" && <ContributeFlow profile={me} db={db} api={api} />}
            {activeTab === "impact" && <Impact db={db} me={me} />}

            {activeTab === "lighthouses" && (
              <Section title="All Lighthouses" icon={MapPin}>
                <ul className="divide-y">
                  {db.lighthouses.map((lh) => (
                    <li key={lh.id} className="py-3 flex items-center justify-between">
                      <div>
                        <p className="font-medium">{lh.name}</p>
                        <p className="text-xs text-neutral-500">Radius ~{lh.radiusKm} km • {lh.dropPoints?.join(", ")}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </Section>
            )}
          </>
        ) : (
          <KeeperView db={db} api={api} />
        )}

        <footer className="pb-12">
          <div className="mt-6 flex items-center justify-center gap-2 text-sm text-neutral-600">
            <span>Questions? WhatsApp us:</span>
            <a
              href="https://wa.me/27662295868"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-full border border-[#D7C5B4] px-3 py-1 hover:bg-[#F7EFE7]"
              aria-label="WhatsApp Just One More at +27 66 229 5868"
            >
              <Phone className="h-4 w-4" />
              <span className="font-medium">+27 66 229 5868</span>
            </a>
          </div>
        </footer>
      </main>

      {showSettings && (
        <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-sm rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                <p className="font-medium">Settings</p>
              </div>
              <button onClick={() => setShowSettings(false)} className="p-2 hover:bg-neutral-100 rounded-xl">
                <X className="h-4 w-4" />
              </button>
            </div>
            <button onClick={() => { api.reset(); setShowSettings(false); }} className="w-full py-3 rounded-2xl border border-[#D7C5B4] hover:bg-[#F7EFE7]">
              Reset demo data
            </button>
            <p className="text-xs text-neutral-500">
              This prototype stores data locally in your browser (no server). For production, we'll use a secure backend (e.g. Supabase/Firebase/Azure) and real push notifications.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
