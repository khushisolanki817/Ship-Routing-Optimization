"""
pages/2_Constraints_Overview.py  —  Constraints Overview + Route Setup
========================================================================
• Interactive constraint cards — click to expand details
• Port & ship selection
• Fuel slider with visual bar
• Storm toggle
• "Calculate All Routes" navigates to page 3
"""

import streamlit as st
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from routing_engine import build_grid, PROTECTED_ZONES, PIRACY_ZONES
from weather_service import preload_weather_grid

st.set_page_config(
    page_title="Maritime DSS — Constraints",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── auth guard ──
if not st.session_state.get("authenticated"):
    st.switch_page("1_Login.py")

# ── CSS ──
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #060f1e; }
[data-testid="stSidebar"]          { display: none; }
[data-testid="collapsedControl"]   { display: none; }
* { color: #c8d8f0; }
h1,h2,h3 { color: #e2ecff !important; }

/* ── SELECTBOX / DROPDOWN dark fix ── */
[data-baseweb="select"] > div,
[data-baseweb="select"] > div:hover,
[data-baseweb="select"] > div:focus-within {
    background-color: #0c1e38 !important;
    border-color: #1e3a5f !important;
    border-radius: 8px !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div[class*="placeholder"],
[data-baseweb="select"] div[class*="singleValue"] {
    color: #c8d8f0 !important;
}
[data-baseweb="select"] svg { fill: #5a7fa8 !important; }

/* dropdown option list */
[data-baseweb="popover"] ul,
[data-baseweb="menu"]    ul,
[role="listbox"]            { background-color: #0c1e38 !important; border: 1px solid #1e3a5f !important; }
[role="option"]             { background-color: #0c1e38 !important; color: #c8d8f0 !important; }
[role="option"]:hover,
[role="option"][aria-selected="true"] { background-color: #122840 !important; color: #e2ecff !important; }

/* ── NUMBER INPUT dark fix ── */
[data-testid="stNumberInput"] input,
[data-baseweb="input"] input  {
    background-color: #0c1e38 !important;
    color: #c8d8f0 !important;
    border-color: #1e3a5f !important;
    border-radius: 8px !important;
}
[data-baseweb="input"]        { background-color: #0c1e38 !important; border-color: #1e3a5f !important; border-radius: 8px !important; }
[data-testid="stNumberInput"] button { background-color: #0c1e38 !important; border-color: #1e3a5f !important; color: #c8d8f0 !important; }

/* ── SLIDER track ── */
[data-testid="stSlider"] [data-baseweb="slider"] div[class*="Track"] { background: #1a3050 !important; }

/* ── TOGGLE ── */
[data-testid="stToggle"] label { color: #c8d8f0 !important; }

/* ── LABELS above widgets ── */
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSlider"] label { color: #7a9cc0 !important; font-size: 13px !important; }

/* ── top nav bar ── */
.topnav {
    display: flex; align-items: center; justify-content: space-between;
    background: #08152a; border-bottom: 1px solid #112240;
    padding: 10px 24px; margin: -1rem -1rem 1.5rem;
}
.nav-logo  { font-size: 18px; font-weight: 700; color: #e2ecff; }
.nav-steps { display: flex; gap: 0; }
.step      { padding: 6px 20px; font-size: 12px; font-weight: 500; color: #3a6080; border-bottom: 2px solid transparent; }
.step.done { color: #1D9E75; border-color: #1D9E75; }
.step.active { color: #e2ecff; border-color: #3b82f6; }
.nav-user  { font-size: 12px; color: #3a6080; background: #0c1e38; border: 1px solid #1a3050; border-radius: 20px; padding: 4px 12px; }

/* constraint cards */
.c-card {
    background: #0a1a30; border: 1.5px solid #1a3050;
    border-radius: 12px; padding: 18px 18px 14px;
    cursor: pointer; transition: border-color .18s, background .18s;
    position: relative; overflow: hidden;
}
.c-card:hover  { border-color: #2a5a8a; background: #0c2040; }
.c-card.active { border-color: #1D9E75; background: #081f18; }
.c-card-icon  { font-size: 26px; margin-bottom: 8px; }
.c-card-title { font-size: 14px; font-weight: 600; color: #e2ecff; margin-bottom: 4px; }
.c-card-sub   { font-size: 12px; color: #5a7fa8; line-height: 1.5; }
.c-card-badge { position: absolute; top: 12px; right: 12px; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }
.badge-danger { background: #3b0f0f; color: #f87171; }
.badge-warn   { background: #3b2600; color: #fbbf24; }
.badge-safe   { background: #083d20; color: #34d399; }
.badge-info   { background: #082040; color: #60a5fa; }

/* detail expand box */
.detail-panel { background: #081830; border: 1px solid #1a3050; border-radius: 10px; padding: 16px 20px; margin: 8px 0 16px; font-size: 13px; color: #7a9cc0; line-height: 1.8; }
.detail-panel h4 { color: #e2ecff; font-size: 14px; margin-bottom: 8px; }
.detail-panel .row { display: flex; justify-content: space-between; border-bottom: 1px solid #112240; padding: 5px 0; }
.detail-panel .row:last-child { border-bottom: none; }
.detail-panel .key { color: #5a7fa8; }
.detail-panel .val { color: #a8c0d8; font-weight: 500; }

/* mode selector */
.mode-btn { background: #0c1e38; border: 1.5px solid #1a3050; border-radius: 10px; padding: 14px 12px; text-align: center; cursor: pointer; transition: border-color .15s, background .15s; }
.mode-btn:hover      { border-color: #2a5a8a; }
.mode-btn.sel-safety { border-color: #1D9E75; background: #081f18; }
.mode-btn.sel-fuel   { border-color: #f59e0b; background: #1f1200; }
.mode-btn.sel-speed  { border-color: #3b82f6; background: #061428; }
.mode-btn-icon  { font-size: 22px; margin-bottom: 6px; }
.mode-btn-label { font-size: 13px; font-weight: 600; color: #e2ecff; }
.mode-btn-sub   { font-size: 11px; color: #5a7fa8; margin-top: 2px; }

/* fuel bar */
.fuel-wrap  { background: #0c1e38; border: 1px solid #1a3050; border-radius: 8px; padding: 10px 14px; margin: 6px 0; }
.fuel-track { height: 7px; border-radius: 4px; background: #1a3050; overflow: hidden; margin-top: 6px; }
.fuel-fill  { height: 100%; border-radius: 4px; }

/* section labels */
.sec-hdr { font-size: 11px; font-weight: 700; color: #3a6080; text-transform: uppercase; letter-spacing: .08em; margin: 18px 0 8px; }
</style>
""", unsafe_allow_html=True)

# ── constants ──
PORT_DATA = {
    "Mumbai, India":          [18.93, 72.83],
    "Chennai, India":         [13.08, 80.28],
    "Karachi, Pakistan":      [24.86, 67.01],
    "Colombo, Sri Lanka":     [6.92,  79.86],
    "Singapore Port":         [1.26,  103.83],
    "Aden, Yemen":            [12.78, 45.01],
    "Mauritius (Port Louis)": [-20.1, 57.5 ],
    "Mombasa, Kenya":         [-4.05, 39.67],
    "Djibouti":               [11.59, 43.14],
}
SHIP_PROFILES = {
    "Container Ship": {"speed":{"safety":13,"fuel":10,"speed":20},"fuel_factor":{"safety":1.0,"fuel":0.72,"speed":1.5}},
    "Tanker":         {"speed":{"safety":11,"fuel":9, "speed":15},"fuel_factor":{"safety":1.1,"fuel":0.80,"speed":1.6}},
    "Bulk Carrier":   {"speed":{"safety":12,"fuel":10,"speed":16},"fuel_factor":{"safety":1.0,"fuel":0.75,"speed":1.4}},
    "Passenger Ship": {"speed":{"safety":18,"fuel":14,"speed":22},"fuel_factor":{"safety":0.9,"fuel":0.85,"speed":1.3}},
    "Naval Vessel":   {"speed":{"safety":22,"fuel":18,"speed":30},"fuel_factor":{"safety":0.8,"fuel":0.80,"speed":1.2}},
}
CONSTRAINTS_INFO = [
    {
        "id": "weather",
        "icon": "🌀",
        "title": "Weather Penalty",
        "sub": "Dynamic storm & wind avoidance",
        "badge": "Critical", "badge_cls": "badge-danger",
        "detail": {
            "What it does": "Assigns a penalty multiplier (1× – 25×) to ocean grid nodes based on wind speed and storm intensity",
            "Safety mode": "^1.3 amplification — route aggressively avoids bad weather",
            "Fuel mode":   "×0.8 — moderate tolerance, prefers calmer seas",
            "Speed mode":  "×0.4 — accepts weather risk for shorter path",
            "Data source": "Physics-based Indian Ocean simulation (instant, no API)",
            "Zones covered": "Bay of Bengal cyclones, Arabian Sea monsoon, Agulhas turbulence",
        }
    },
    {
        "id": "piracy",
        "icon": "⚠️",
        "title": "Piracy Risk Zones",
        "sub": "Gulf of Aden & Somali Coast",
        "badge": "High Risk", "badge_cls": "badge-danger",
        "detail": {
            "What it does": "Marks Gulf of Aden (400 NM) and Somali Coast (250 NM) as high-cost zones",
            "Safety mode": "15× cost penalty — route avoids zone entirely",
            "Fuel mode":   "8× penalty — avoids unless major detour needed",
            "Speed mode":  "8× penalty — still avoids high-risk areas",
            "Zones": "Gulf of Aden: 12°N 45°E r=400 NM · Somali: 2°N 49°E r=250 NM",
        }
    },
    {
        "id": "marine",
        "icon": "🌿",
        "title": "Marine Protected Zones",
        "sub": "Environmental compliance",
        "badge": "Protected", "badge_cls": "badge-safe",
        "detail": {
            "What it does": "Penalises routing through UNESCO/international marine reserves",
            "Penalty": "Up to 5× based on proximity to zone centre",
            "Zones": "Chagos Marine Reserve, Lakshadweep Sanctuary, Mozambique Channel Coral, Madagascar Marine Park",
            "All modes": "Same penalty across all 3 modes — environmental compliance is non-negotiable",
        }
    },
    {
        "id": "fuel",
        "icon": "⛽",
        "title": "Fuel Level Constraint",
        "sub": "Conservative routing when low",
        "badge": "Adaptive", "badge_cls": "badge-warn",
        "detail": {
            "What it does": "When fuel < 40%, penalises westward movement against monsoon currents",
            "Low fuel (<40%)": "2× penalty on westward nodes + (2.0 - fuel/100) multiplier",
            "Critical (<25%)": "Max efficiency routing, avoids any unnecessary distance",
            "Ocean currents": "Fuel mode uses Agulhas & monsoon currents for 0.85–0.92× cost discount",
            "Ship type": "Each vessel has different fuel burn rates (Tanker vs Naval Vessel etc.)",
        }
    },
    {
        "id": "obstacle",
        "icon": "🌊",
        "title": "Real-time Obstacles",
        "sub": "Dynamic storm & blockage replanning",
        "badge": "Live", "badge_cls": "badge-info",
        "detail": {
            "What it does": "Simulates a storm/obstacle at a user-defined location with custom radius",
            "Mechanism": "All grid nodes within the obstacle radius are added to a 'blocked' set",
            "A* behaviour": "Blocked nodes are completely skipped during pathfinding — forced detour",
            "Result": "Route automatically replans around the obstacle in real-time",
            "Use case": "Test ship replanning when a cyclone forms mid-route",
        }
    },
    {
        "id": "distance",
        "icon": "📐",
        "title": "Distance Heuristic",
        "sub": "A* Haversine heuristic guide",
        "badge": "Algorithm", "badge_cls": "badge-info",
        "detail": {
            "What it does": "A* uses Haversine great-circle distance as the heuristic to guide search",
            "Why Haversine": "More accurate than Euclidean on spherical Earth (important at Indian Ocean scale)",
            "Speed mode":    "Heuristic weight is highest — guides A* more aggressively toward goal",
            "Safety mode":   "Heuristic balanced with heavy weather/piracy penalties",
            "Smoothing":     "Douglas-Peucker algorithm removes redundant waypoints after pathfinding",
        }
    },
]

# ── one-time grid init ──
if st.session_state.nodes is None:
    with st.spinner("Building Indian Ocean navigation grid…"):
        from routing_engine import build_grid
        n, t, g = build_grid(step=2.5)
        st.session_state.nodes = n
        st.session_state.tree  = t
        st.session_state.graph = g

if not st.session_state.weather_loaded:
    with st.spinner("Computing weather simulation…"):
        preload_weather_grid()
        st.session_state.weather_loaded = True

# ── top nav ──
uname = st.session_state.get("username","user")
urole = st.session_state.get("user_role","Officer")
st.markdown(f"""
<div class="topnav">
  <div class="nav-logo">🚢 Maritime DSS</div>
  <div class="nav-steps">
    <div class="step done">① Login</div>
    <div class="step active">② Constraints</div>
    <div class="step">③ Route Map</div>
    <div class="step">④ Summary</div>
  </div>
  <div class="nav-user">👤 {uname} · {urole}</div>
</div>
""", unsafe_allow_html=True)

_lc, _rc = st.columns([6, 1])
with _rc:
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        st.session_state.authenticated  = False
        st.session_state.username       = ""
        st.session_state.all_routes     = {}
        st.session_state.all_stats      = {}
        st.session_state.route_params   = {}
        st.session_state.replan_log     = []
        st.session_state.route_calculated = False
        st.switch_page("1_Login.py")

st.markdown("<h2 style='margin:0 0 4px'>Constraints Overview</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#3a6080;font-size:13px;margin:0 0 20px'>Click any constraint card to see exactly how it affects routing</p>", unsafe_allow_html=True)

# ── constraint cards ──
if "expanded_constraint" not in st.session_state:
    st.session_state.expanded_constraint = None

cols = st.columns(3)
for i, c in enumerate(CONSTRAINTS_INFO):
    with cols[i % 3]:
        is_active = st.session_state.expanded_constraint == c["id"]
        active_cls = "active" if is_active else ""
        st.markdown(f"""
<div class="c-card {active_cls}" onclick="">
  <span class="c-card-badge {c['badge_cls']}">{c['badge']}</span>
  <div class="c-card-icon">{c['icon']}</div>
  <div class="c-card-title">{c['title']}</div>
  <div class="c-card-sub">{c['sub']}</div>
</div>
""", unsafe_allow_html=True)
        if st.button(f"{'▼ Hide' if is_active else '▶ Details'}", key=f"cbtn_{c['id']}", use_container_width=True):
            st.session_state.expanded_constraint = None if is_active else c["id"]
            st.rerun()

# ── expanded detail panel ──
expanded = next((c for c in CONSTRAINTS_INFO if c["id"] == st.session_state.expanded_constraint), None)
if expanded:
    rows_html = "".join(
        f'<div class="row"><span class="key">{k}</span><span class="val">{v}</span></div>'
        for k, v in expanded["detail"].items()
    )
    st.markdown(f"""
<div class="detail-panel">
  <h4>{expanded['icon']} {expanded['title']} — How it works</h4>
  {rows_html}
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#112240;margin:24px 0'>", unsafe_allow_html=True)

# ── route setup ──
st.markdown("<h3 style='margin:0 0 4px'>Route Configuration</h3>", unsafe_allow_html=True)
st.markdown("<p style='color:#3a6080;font-size:13px;margin:0 0 16px'>Set your voyage parameters, then calculate all 3 constraint-based paths</p>", unsafe_allow_html=True)

left, right = st.columns([3, 2])

with left:
    st.markdown('<div class="sec-hdr">Ports</div>', unsafe_allow_html=True)
    ports = list(PORT_DATA.keys())
    c1, c2 = st.columns(2)
    with c1:
        start_p = st.selectbox("🟢 Origin",      ports, index=0)
    with c2:
        end_p   = st.selectbox("🔴 Destination", ports, index=6)
    if start_p == end_p:
        st.error("Origin and destination must differ.")

    st.markdown('<div class="sec-hdr">Vessel type</div>', unsafe_allow_html=True)
    ship_type = st.selectbox("", list(SHIP_PROFILES.keys()), label_visibility="collapsed")

    st.markdown('<div class="sec-hdr">Fuel level</div>', unsafe_allow_html=True)
    fuel_pct = st.slider("fuel", 10, 100, 80, 5, label_visibility="collapsed")
    fuel_color = "#34d399" if fuel_pct>=50 else "#fbbf24" if fuel_pct>=25 else "#f87171"
    fuel_status = "Normal" if fuel_pct>=50 else "Low — conservative routing" if fuel_pct>=25 else "Critical — max efficiency"
    st.markdown(f"""
<div class="fuel-wrap">
  <div style="display:flex;justify-content:space-between">
    <span style="font-size:13px;font-weight:700;color:#e2ecff">{fuel_pct}%</span>
    <span style="font-size:11px;color:{fuel_color}">{fuel_status}</span>
  </div>
  <div class="fuel-track"><div class="fuel-fill" style="width:{fuel_pct}%;background:{fuel_color}"></div></div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">Real-time obstacle</div>', unsafe_allow_html=True)
    obstacle_active = st.toggle("Simulate storm / obstacle")
    obs_lat, obs_lon, obs_radius = 5.0, 75.0, 200
    if obstacle_active:
        oc1, oc2, oc3 = st.columns(3)
        with oc1: obs_lat    = st.number_input("Lat",  -25.0, 20.0,  5.0, 0.5)
        with oc2: obs_lon    = st.number_input("Lon",   35.0, 105.0, 75.0, 0.5)
        with oc3: obs_radius = st.number_input("Radius NM", 50, 600, 200, 50)
        st.warning(f"Storm at {obs_lat}°N, {obs_lon}°E — {obs_radius} NM")

with right:
    st.markdown('<div class="sec-hdr">Primary constraint (highlighted path)</div>', unsafe_allow_html=True)
    MODE_META = {
        "safety": {"label":"Safety First",   "icon":"🛡️", "sub":"Avoid storms & piracy",  "color":"#1D9E75"},
        "fuel":   {"label":"Fuel Efficient",  "icon":"⛽",  "sub":"Use ocean currents",     "color":"#f59e0b"},
        "speed":  {"label":"Max Speed",       "icon":"⚡",  "sub":"Shortest path",          "color":"#3b82f6"},
    }
    sel = st.session_state.get("current_mode","safety")
    for mk, meta in MODE_META.items():
        sel_cls = f"sel-{mk}" if sel==mk else ""
        st.markdown(f"""
<div class="mode-btn {sel_cls}">
  <div class="mode-btn-icon">{meta['icon']}</div>
  <div class="mode-btn-label">{meta['label']}</div>
  <div class="mode-btn-sub">{meta['sub']}</div>
</div>
""", unsafe_allow_html=True)
        if st.button(f"Select {meta['label']}", key=f"sel_{mk}", use_container_width=True):
            st.session_state.current_mode = mk
            st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # summary of what will be calculated
    st.markdown(f"""
<div style="background:#081830;border:1px solid #1a3050;border-radius:10px;padding:14px 16px;font-size:12px;color:#5a7fa8;line-height:1.9">
  <b style="color:#e2ecff">Will calculate 3 paths:</b><br>
  🛡️ <span style="color:#1D9E75">Safety</span> — storm/piracy avoidance<br>
  ⛽ <span style="color:#f59e0b">Fuel</span> — current-optimised<br>
  ⚡ <span style="color:#3b82f6">Speed</span> — shortest great-circle<br><br>
  <b style="color:#e2ecff">Highlighted:</b> <span style="color:{MODE_META[st.session_state.current_mode]['color']}">{MODE_META[st.session_state.current_mode]['icon']} {MODE_META[st.session_state.current_mode]['label']}</span>
</div>
""", unsafe_allow_html=True)

# ── calculate button ──
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
b1, b2, b3 = st.columns([2, 1, 1])
with b1:
    go = st.button("🗺️  Calculate All Routes → View Map",
                   type="primary", disabled=(start_p==end_p),
                   use_container_width=True)
with b3:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.switch_page("1_Login.py")

if go and start_p != end_p:
    # store params in session state for page 3
    st.session_state.route_params = {
        "start_p": start_p, "end_p": end_p,
        "ship_type": ship_type, "fuel_pct": fuel_pct,
        "obstacle_active": obstacle_active,
        "obs_lat": obs_lat, "obs_lon": obs_lon, "obs_radius": obs_radius,
    }
    st.session_state.route_calculated = False   # force recalc on page 3
    st.switch_page("pages/3_Route_Map.py")
