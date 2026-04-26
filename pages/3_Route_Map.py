"""
pages/3_Route_Map.py  —  Route Map (UPDATED)
=============================================
✅ All 3 paths always visible on map
✅ Selected path: thick + bright + solid
✅ Other paths: thinner + semi-transparent + dashed
✅ Each path has unique color (green / amber / blue)
✅ Click any path → detailed popup
✅ Mid-route distance badge on each path
✅ Path selector buttons show live stats
✅ Selected path detail panel below map
"""

import streamlit as st
from streamlit_folium import st_folium
import folium
import numpy as np
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from routing_engine import (
    build_grid, dynamic_astar, haversine_nm,
    analyze_route, PROTECTED_ZONES, PIRACY_ZONES,
)
from weather_service import get_live_weather_penalty, get_weather_description

st.set_page_config(
    page_title="Maritime DSS — Route Map",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if not st.session_state.get("authenticated"):
    st.switch_page("Login.py")

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
[data-baseweb="select"] > div,
[data-baseweb="select"] > div:hover,
[data-baseweb="select"] > div:focus-within {
    background-color: #0c1e38 !important;
    border-color: #1e3a5f !important; border-radius: 8px !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div[class*="placeholder"],
[data-baseweb="select"] div[class*="singleValue"] { color: #c8d8f0 !important; }
[data-baseweb="select"] svg { fill: #5a7fa8 !important; }
[data-baseweb="popover"] ul, [data-baseweb="menu"] ul, [role="listbox"]
    { background-color: #0c1e38 !important; border: 1px solid #1e3a5f !important; }
[role="option"] { background-color: #0c1e38 !important; color: #c8d8f0 !important; }
[role="option"]:hover,
[role="option"][aria-selected="true"] { background-color: #122840 !important; color: #e2ecff !important; }
[data-testid="stNumberInput"] input, [data-baseweb="input"] input
    { background-color: #0c1e38 !important; color: #c8d8f0 !important; border-color: #1e3a5f !important; border-radius: 8px !important; }
[data-baseweb="input"] { background-color: #0c1e38 !important; border-color: #1e3a5f !important; border-radius: 8px !important; }
[data-testid="stNumberInput"] button { background-color: #0c1e38 !important; border-color: #1e3a5f !important; color: #c8d8f0 !important; }
[data-testid="stSelectbox"] label, [data-testid="stNumberInput"] label,
[data-testid="stSlider"] label { color: #7a9cc0 !important; font-size: 13px !important; }
[data-testid="stAppViewContainer"] { background: #060f1e; }
[data-testid="stSidebar"]          { display: none; }
[data-testid="collapsedControl"]   { display: none; }
section[data-testid="stSidebarNav"]{ display: none; }
* { color: #c8d8f0; }
h1,h2,h3 { color: #e2ecff !important; }

.topnav {
    display:flex; align-items:center; justify-content:space-between;
    background:#08152a; border-bottom:1px solid #112240;
    padding:10px 24px; margin:-1rem -1rem 1.5rem;
}
.nav-logo  { font-size:18px; font-weight:700; color:#e2ecff; }
.nav-steps { display:flex; gap:0; }
.step      { padding:6px 20px; font-size:12px; font-weight:500; color:#3a6080; border-bottom:2px solid transparent; }
.step.done { color:#1D9E75; border-color:#1D9E75; }
.step.active { color:#e2ecff; border-color:#3b82f6; }
.nav-user  { font-size:12px; color:#3a6080; background:#0c1e38; border:1px solid #1a3050; border-radius:20px; padding:4px 12px; }

/* Path selector buttons */
.path-sel-card {
    border-radius:10px; padding:12px 14px; margin-bottom:4px;
    cursor:pointer; transition:border .15s, background .15s;
}

/* Metric cards */
.m-card  { background:#0a1a30; border:1px solid #1a3050; border-radius:10px; padding:12px 16px; text-align:center; }
.m-label { font-size:11px; color:#5a7fa8; text-transform:uppercase; letter-spacing:.06em; }
.m-value { font-size:20px; font-weight:700; color:#e2ecff; line-height:1.2; }
.m-unit  { font-size:11px; color:#5a7fa8; }
.m-badge { display:inline-block; font-size:10px; font-weight:600; border-radius:6px; padding:2px 7px; margin-top:4px; }
.badge-ok   { background:#083d20; color:#34d399; }
.badge-warn { background:#3b2600; color:#fbbf24; }
.badge-bad  { background:#3b0f0f; color:#f87171; }
.badge-blue { background:#082040; color:#60a5fa; }

/* Detail cards */
.detail-card { background:#081830; border:1px solid #1a3050; border-radius:10px; padding:16px 18px; margin-top:8px; font-size:12px; color:#7a9cc0; line-height:1.9; }
.detail-card h4 { color:#e2ecff; font-size:14px; margin-bottom:10px; }
.d-row { display:flex; justify-content:space-between; border-bottom:1px solid #112240; padding:4px 0; }
.d-row:last-child { border-bottom:none; }
.d-key { color:#5a7fa8; } .d-val { color:#a8c0d8; font-weight:500; }

.chip { display:inline-block; font-size:11px; border-radius:6px; padding:3px 9px; margin:2px; }
.chip-teal  { background:#083d30; color:#34d399; border:1px solid #0f6a50; }
.chip-amber { background:#3b2600; color:#fbbf24; border:1px solid #7a5200; }
.chip-red   { background:#3b0f0f; color:#f87171; border:1px solid #7a1a1a; }
.chip-blue  { background:#082040; color:#60a5fa; border:1px solid #1a4a80; }

.legend-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.sec-hdr { font-size:11px; font-weight:700; color:#3a6080; text-transform:uppercase; letter-spacing:.08em; margin:14px 0 8px; }

/* path comparison mini-table */
.path-cmp { width:100%; border-collapse:collapse; font-size:12px; }
.path-cmp th { background:#0c1e38; color:#5a7fa8; font-size:10px; font-weight:600; text-transform:uppercase; padding:7px 10px; border-bottom:1px solid #1a3050; }
.path-cmp td { padding:7px 10px; border-bottom:1px solid #112240; color:#a8c0d8; }
.path-cmp tr:hover td { background:#0a1a30; }
.best-val { color:#34d399 !important; font-weight:700 !important; }
</style>
""", unsafe_allow_html=True)

# ── constants ────────────────────────────────────────────────
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
MODE_META = {
    "safety": {"label":"Safety First",   "icon":"🛡️", "sub":"Storm & piracy avoidance",   "color":"#1D9E75"},
    "fuel":   {"label":"Fuel Efficient",  "icon":"⛽",  "sub":"Ocean current optimised",    "color":"#f59e0b"},
    "speed":  {"label":"Max Speed",       "icon":"⚡",  "sub":"Shortest great-circle path", "color":"#3b82f6"},
}


def douglas_peucker(points, epsilon=0.3):
    if len(points) < 3: return points
    dmax, idx = 0.0, 0
    start, end = np.array(points[0]), np.array(points[-1])
    line = end - start
    norm = np.linalg.norm(line)
    for i in range(1, len(points)-1):
        d = (np.linalg.norm(np.cross(line, start-np.array(points[i])))/norm
             if norm > 0 else np.linalg.norm(np.array(points[i])-start))
        if d > dmax: dmax, idx = d, i
    if dmax > epsilon:
        return douglas_peucker(points[:idx+1], epsilon)[:-1] + douglas_peucker(points[idx:], epsilon)
    return [points[0], points[-1]]


def apply_ship_profile(stats_dict, m_mode, ship):
    sp = SHIP_PROFILES[ship]
    d  = stats_dict["distance_nm"]
    stats_dict["speed_knots"]   = sp["speed"][m_mode]
    stats_dict["est_hours"]     = round(d / sp["speed"][m_mode], 1)
    stats_dict["est_days"]      = round(d / sp["speed"][m_mode] / 24, 1)
    stats_dict["est_fuel_tons"] = round((d / 100) * sp["fuel_factor"][m_mode], 1)
    return stats_dict


# ── top nav ──────────────────────────────────────────────────
uname = st.session_state.get("username", "user")
urole = st.session_state.get("user_role", "Officer")
st.markdown(f"""
<div class="topnav">
  <div class="nav-logo">🚢 Maritime DSS</div>
  <div class="nav-steps">
    <div class="step done">① Login</div>
    <div class="step done">② Constraints</div>
    <div class="step active">③ Route Map</div>
    <div class="step">④ Summary</div>
  </div>
  <div class="nav-user">👤 {uname} · {urole}</div>
</div>
""", unsafe_allow_html=True)

_lc, _rc = st.columns([6, 1])
with _rc:
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        for k in ["authenticated","username","all_routes","all_stats","route_params","replan_log","route_calculated"]:
            st.session_state[k] = False if k == "authenticated" else ({} if k in ["all_routes","all_stats","route_params"] else ([] if k == "replan_log" else ("" if k == "username" else False)))
        st.switch_page("Login.py")

# ── get params ───────────────────────────────────────────────
params = st.session_state.get("route_params", {})
if not params:
    st.warning("No route configured. Please go back and set voyage parameters.")
    if st.button("← Back to Constraints"):
        st.switch_page("pages/2_Constraints_Overview.py")
    st.stop()

start_p         = params["start_p"]
end_p           = params["end_p"]
ship_type       = params["ship_type"]
fuel_pct        = params["fuel_pct"]
obstacle_active = params["obstacle_active"]
obs_lat         = params.get("obs_lat", 5.0)
obs_lon         = params.get("obs_lon", 75.0)
obs_radius      = params.get("obs_radius", 200)

nodes = st.session_state.nodes
tree  = st.session_state.tree
graph = st.session_state.graph

# ── calculate all 3 routes (once) ────────────────────────────
if not st.session_state.route_calculated:
    blocked = set()
    if obstacle_active:
        for i, nd in enumerate(nodes):
            if haversine_nm(nd, [obs_lat, obs_lon]) < obs_radius:
                blocked.add(i)

    all_routes = {}
    all_stats  = {}
    s_idx = tree.query(PORT_DATA[start_p])[1]
    e_idx = tree.query(PORT_DATA[end_p])[1]

    with st.status("Calculating all 3 routes…", expanded=True) as status:
        for mk in ["safety", "fuel", "speed"]:
            st.write(f"Computing {MODE_META[mk]['icon']} **{mk}** route…")
            route, _ = dynamic_astar(
                s_idx, e_idx, nodes, graph,
                mode=mk, fuel_level_pct=fuel_pct, blocked_nodes=blocked
            )
            if route:
                coords = [nodes[i].tolist() for i in route]
                raw_s  = analyze_route(route, nodes, mk)
                stats  = apply_ship_profile(raw_s, mk, ship_type)
                all_routes[mk] = coords
                all_stats[mk]  = stats
                st.write(f"  ✅ {stats['distance_nm']} NM · {stats['est_hours']} hrs")
            else:
                st.write(f"  ❌ No route found for {mk} mode")

        st.session_state.all_routes       = all_routes
        st.session_state.all_stats        = all_stats
        st.session_state.route_calculated = True
        if obstacle_active:
            st.session_state.replan_log.append({
                "ts": datetime.now().strftime("%H:%M:%S"), "level": "warn",
                "msg": f"Storm at ({obs_lat}°N, {obs_lon}°E) {obs_radius} NM — all routes replanned"
            })
        status.update(label="✅ All 3 routes calculated!", state="complete")

all_routes = st.session_state.all_routes
all_stats  = st.session_state.all_stats

if not all_routes:
    st.error("Route calculation failed. Please go back.")
    st.stop()

# ── page header ──────────────────────────────────────────────
st.markdown("<h2 style='margin:0 0 2px'>Route Map</h2>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:#3a6080;font-size:13px;margin:0 0 16px'>"
    f"{start_p} → {end_p} · {ship_type} · Fuel {fuel_pct}%</p>",
    unsafe_allow_html=True
)

# ── PATH SELECTOR ROW ─────────────────────────────────────────
# 3 path cards + navigation
sel_mode = st.session_state.get("current_mode", "safety")
sel_cols = st.columns([3, 3, 3, 2])

for i, (mk, meta) in enumerate(MODE_META.items()):
    with sel_cols[i]:
        s      = all_stats.get(mk, {})
        is_sel = (mk == sel_mode)
        border = f"2px solid {meta['color']}" if is_sel else "1.5px solid #1a3050"
        bg     = f"#081428" if mk == "speed" and is_sel else \
                 f"#081f10" if mk == "safety" and is_sel else \
                 f"#1a1000" if mk == "fuel"   and is_sel else "#0a1a30"

        wx    = s.get("avg_weather_index", 0)
        wx_c  = "#34d399" if wx < 3 else "#fbbf24" if wx < 6 else "#f87171"
        wx_lbl= "Clear" if wx < 3 else "Moderate" if wx < 6 else "Rough"

        co2   = round(s.get("est_fuel_tons", 0) * 3.17, 1)

        st.markdown(f"""
<div style="background:{bg};border:{border};border-radius:10px;padding:12px 14px;margin-bottom:4px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
    <span style="font-size:20px">{meta['icon']}</span>
    <div>
      <div style="font-size:13px;font-weight:700;color:{meta['color']}">{meta['label']}</div>
      <div style="font-size:10px;color:#3a6080">{meta['sub']}</div>
    </div>
    {'<div style="margin-left:auto;font-size:9px;color:#1D9E75;font-weight:700;background:#083d20;padding:2px 7px;border-radius:8px">SELECTED</div>' if is_sel else ''}
  </div>
  <div style="display:flex;gap:12px;font-size:11px;flex-wrap:wrap">
    <span>📍 <b style="color:#e2ecff">{s.get('distance_nm',0):.0f} NM</b></span>
    <span>⏱️ <b style="color:#e2ecff">{s.get('est_hours',0):.0f} h</b></span>
    <span>⛽ <b style="color:#e2ecff">{s.get('est_fuel_tons',0):.1f} t</b></span>
    <span style="color:{wx_c}">🌊 {wx_lbl}</span>
  </div>
</div>""", unsafe_allow_html=True)

        btn_label = "✓ Selected" if is_sel else f"Select {meta['icon']}"
        if st.button(btn_label, key=f"pathsel_{mk}", use_container_width=True,
                     type="primary" if is_sel else "secondary"):
            st.session_state.current_mode = mk
            st.rerun()

with sel_cols[3]:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("← Constraints",  use_container_width=True):
        st.switch_page("pages/2_Constraints_Overview.py")
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("Summary →", type="primary", use_container_width=True):
        st.switch_page("pages/4_Summary.py")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── BUILD MAP ─────────────────────────────────────────────────
m = folium.Map(location=[3, 68], zoom_start=4, tiles="CartoDB dark_matter")

# Draw routes — NON-selected first (so selected renders on top)
draw_order = [mk for mk in ["safety","fuel","speed"] if mk != sel_mode] + [sel_mode]

for mk in draw_order:
    if mk not in all_routes:
        continue

    meta   = MODE_META[mk]
    coords = all_routes[mk]
    smooth = douglas_peucker(coords, 0.25)
    s      = all_stats.get(mk, {})
    is_sel = (mk == sel_mode)

    # Visual styling: selected = thick+bright, others = thin+faded
    weight  = 6   if is_sel else 2.5
    opacity = 0.95 if is_sel else 0.40
    dash    = None if is_sel else "8 6"

    # ── Popup HTML ─────────────────────────────────────────
    wx_w = {"safety": "^1.3 — storm penalty amplified",
            "fuel":   "×0.8 — moderate tolerance",
            "speed":  "×0.4 — mostly ignored"}[mk]
    pi_w = "15× (strong avoidance)" if mk == "safety" else "8× (moderate avoidance)"
    cur  = "0.85–0.92× discount (Agulhas / monsoon)" if mk == "fuel" else "Not applied"
    co2  = round(s.get("est_fuel_tons", 0) * 3.17, 1)

    popup_html = f"""
<div style="font-family:system-ui,sans-serif;min-width:270px;max-width:300px;
            background:#0a1628;color:#c8d8f0;border-radius:10px;
            padding:14px 16px;font-size:12px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
    <span style="font-size:22px">{meta['icon']}</span>
    <div>
      <div style="font-size:15px;font-weight:700;color:{meta['color']}">{meta['label']}</div>
      <div style="font-size:10px;color:#3a6080">{meta['sub']}</div>
    </div>
  </div>
  <table style="width:100%;border-collapse:collapse;margin-bottom:10px">
    <tr style="border-bottom:1px solid #1a3050">
      <td style="color:#5a7fa8;padding:4px 0">Distance</td>
      <td style="text-align:right;color:#e2ecff;font-weight:700">{s.get('distance_nm',0):.0f} NM</td>
    </tr>
    <tr style="border-bottom:1px solid #1a3050">
      <td style="color:#5a7fa8;padding:4px 0">Duration</td>
      <td style="text-align:right;color:#e2ecff;font-weight:700">{s.get('est_hours',0):.0f} hrs · {s.get('est_days',0):.1f}d</td>
    </tr>
    <tr style="border-bottom:1px solid #1a3050">
      <td style="color:#5a7fa8;padding:4px 0">Speed</td>
      <td style="text-align:right;color:#e2ecff;font-weight:700">{s.get('speed_knots',0)} kts</td>
    </tr>
    <tr style="border-bottom:1px solid #1a3050">
      <td style="color:#5a7fa8;padding:4px 0">Fuel estimate</td>
      <td style="text-align:right;color:#e2ecff;font-weight:700">{s.get('est_fuel_tons',0):.1f} t</td>
    </tr>
    <tr style="border-bottom:1px solid #1a3050">
      <td style="color:#5a7fa8;padding:4px 0">CO₂ estimate</td>
      <td style="text-align:right;color:#e2ecff;font-weight:700">{co2} kg</td>
    </tr>
    <tr style="border-bottom:1px solid #1a3050">
      <td style="color:#5a7fa8;padding:4px 0">Avg weather</td>
      <td style="text-align:right;color:#e2ecff;font-weight:700">{s.get('avg_weather_index',0):.2f}</td>
    </tr>
    <tr>
      <td style="color:#5a7fa8;padding:4px 0">Waypoints</td>
      <td style="text-align:right;color:#e2ecff;font-weight:700">{s.get('waypoints',0)}</td>
    </tr>
  </table>
  <div style="background:#061428;border-radius:6px;padding:8px 10px;font-size:11px;line-height:1.8">
    <div style="color:#a8c0d8;font-weight:600;margin-bottom:4px">Active Constraints</div>
    <div style="color:#5a7fa8">Weather: <span style="color:#a8c0d8">{wx_w}</span></div>
    <div style="color:#5a7fa8">Piracy:  <span style="color:#a8c0d8">{pi_w}</span></div>
    <div style="color:#5a7fa8">Marine:  <span style="color:#a8c0d8">Up to 5× (all modes)</span></div>
    <div style="color:#5a7fa8">Currents:<span style="color:#a8c0d8"> {cur}</span></div>
  </div>
</div>"""

    fg = folium.FeatureGroup(name=f"{meta['icon']} {meta['label']}", show=True)

    line_kwargs = dict(
        locations = smooth,
        color     = meta["color"],
        weight    = weight,
        opacity   = opacity,
        tooltip   = f"{'★ ' if is_sel else ''}{meta['icon']} {meta['label']} · {s.get('distance_nm',0):.0f} NM — click for details",
        popup     = folium.Popup(popup_html, max_width=310),
    )
    if dash:
        line_kwargs["dash_array"] = dash
    folium.PolyLine(**line_kwargs).add_to(fg)

    # Waypoint dots — only on selected path
    if is_sel:
        for coord in smooth[1:-1:5]:
            folium.CircleMarker(
                coord, radius=3, color=meta["color"],
                fill=True, fill_opacity=0.85,
            ).add_to(fg)

    # Mid-route distance label badge on ALL paths
    if len(smooth) > 2:
        mid = smooth[len(smooth) // 2]
        badge_style = (
            f"background:{meta['color']};color:#000;font-weight:700;"
            f"font-size:{'12' if is_sel else '10'}px;"
            f"padding:{'4px 10px' if is_sel else '2px 7px'};"
            f"border-radius:10px;white-space:nowrap;"
            f"box-shadow:0 2px 8px rgba(0,0,0,.6);"
            f"opacity:{'1' if is_sel else '0.75'}"
        )
        folium.Marker(
            mid,
            icon=folium.DivIcon(
                html=f"<div style='{badge_style}'>{meta['icon']} {s.get('distance_nm',0):.0f} NM</div>",
                icon_size=(140, 28), icon_anchor=(70, 14),
            ),
        ).add_to(fg)

    fg.add_to(m)

# ── Port markers ──────────────────────────────────────────────
folium.Marker(
    PORT_DATA[start_p],
    popup=f"<b>ORIGIN</b><br>{start_p}",
    icon=folium.Icon(color="green", icon="anchor", prefix="fa"),
).add_to(m)
folium.Marker(
    PORT_DATA[end_p],
    popup=f"<b>DESTINATION</b><br>{end_p}",
    icon=folium.Icon(color="red", icon="flag", prefix="fa"),
).add_to(m)

# ── Marine protected zones ────────────────────────────────────
for z in PROTECTED_ZONES:
    folium.Circle(
        [z["lat"], z["lon"]], radius=z["radius_nm"] * 1852,
        color="#1D9E75", fill=True, fill_opacity=0.08,
        tooltip=f"🌿 Marine Reserve: {z['name']}",
    ).add_to(m)
    folium.Marker(
        [z["lat"], z["lon"]],
        icon=folium.DivIcon(html='<div style="font-size:13px">🌿</div>',
                            icon_size=(18, 18), icon_anchor=(9, 9)),
    ).add_to(m)

# ── Piracy zones ──────────────────────────────────────────────
for z in PIRACY_ZONES:
    folium.Circle(
        [z["lat"], z["lon"]], radius=z["radius_nm"] * 1852,
        color="#ef4444", fill=True, fill_opacity=0.08,
        tooltip="⚠️ High Piracy Risk Zone",
    ).add_to(m)

# ── Storm obstacle ────────────────────────────────────────────
if obstacle_active:
    folium.Circle(
        [obs_lat, obs_lon], radius=obs_radius * 1852,
        color="#f59e0b", fill=True, fill_opacity=0.25,
        tooltip=f"🌀 Storm — {obs_radius} NM radius",
    ).add_to(m)
    folium.Circle(
        [obs_lat, obs_lon], radius=obs_radius * 1852 * 1.12,
        color="#f59e0b", fill=False, weight=2, dash_array="8",
        tooltip="Avoidance boundary",
    ).add_to(m)
    folium.Marker(
        [obs_lat, obs_lon],
        icon=folium.DivIcon(html='<div style="font-size:22px">🌀</div>',
                            icon_size=(28, 28), icon_anchor=(14, 14)),
    ).add_to(m)

# ── Weather overlay (toggle-able layer) ───────────────────────
wx_fg = folium.FeatureGroup(name="⛅ Weather overlay", show=False)
for slat in np.arange(-25, 22, 10):
    for slon in np.arange(35, 108, 10):
        try:
            from global_land_mask import globe
            if globe.is_land(slat, slon): continue
        except Exception:
            pass
        wp = get_live_weather_penalty(slat, slon)
        if wp > 6.0:
            c = "#ef4444" if wp > 10 else "#f59e0b"
            folium.CircleMarker(
                [slat, slon], radius=min(14, max(5, wp * 1.2)),
                color=c, fill=True, fill_opacity=0.25,
                tooltip=f"{get_weather_description(slat, slon)} ({wp:.1f}×)",
            ).add_to(wx_fg)
wx_fg.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

map_data = st_folium(m, width=None, height=520, returned_objects=["last_object_clicked"])

# ── MAP LEGEND ────────────────────────────────────────────────
legend_items = [
    f"<span class='legend-dot' style='background:#1D9E75'></span><span style='color:#7a9cc0'>Safety path</span>",
    f"<span class='legend-dot' style='background:#f59e0b'></span><span style='color:#7a9cc0'>Fuel path</span>",
    f"<span class='legend-dot' style='background:#3b82f6'></span><span style='color:#7a9cc0'>Speed path</span>",
    f"<span class='legend-dot' style='background:#1D9E75;opacity:.3'></span><span style='color:#7a9cc0'>Marine reserve</span>",
    f"<span class='legend-dot' style='background:#ef4444;opacity:.3'></span><span style='color:#7a9cc0'>Piracy zone</span>",
]
if obstacle_active:
    legend_items.append("<span style='color:#7a9cc0'>🌀 Storm</span>")
legend_items.append("<span style='color:#5a7fa8;font-size:11px'>Thick+bright = selected · Thin+faded = others · Click any path for details</span>")

st.markdown(
    "<div style='display:flex;flex-wrap:wrap;gap:16px;margin-top:8px;align-items:center'>"
    + "  ".join(legend_items) + "</div>",
    unsafe_allow_html=True
)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── SELECTED PATH DETAIL ──────────────────────────────────────
sel_stats = all_stats.get(sel_mode, {})
sel_meta  = MODE_META[sel_mode]

st.markdown(
    f"<h3 style='margin:0 0 10px'>{sel_meta['icon']} {sel_meta['label']} — Active Path Details</h3>",
    unsafe_allow_html=True
)

# metric cards
metric_cols = st.columns(6)
wx_val = sel_stats.get("avg_weather_index", 1.0)
cards  = [
    ("Distance",    f"{sel_stats.get('distance_nm',0):.0f}",    "NM",  "Calculated",                                            "badge-ok"),
    ("Duration",    f"{sel_stats.get('est_hours',0):.0f}",      "hrs", f"{sel_stats.get('est_days',0):.1f}d",                   "badge-ok"),
    ("Speed",       str(sel_stats.get("speed_knots", 0)),        "kts", ship_type.split()[0],                                    "badge-blue"),
    ("Fuel est.",   f"{sel_stats.get('est_fuel_tons',0):.0f}",   "t",   "Normal" if fuel_pct > 40 else "Low fuel mode",         "badge-ok" if fuel_pct > 40 else "badge-warn"),
    ("Avg weather", f"{wx_val:.1f}",                              "",    "Clear" if wx_val<3 else "Moderate" if wx_val<6 else "Rough", "badge-ok" if wx_val<3 else "badge-warn" if wx_val<6 else "badge-bad"),
    ("Waypoints",   str(sel_stats.get("waypoints", 0)),           "",   "Smoothed",                                              "badge-ok"),
]
for col, (lbl, val, unit, badge, bcls) in zip(metric_cols, cards):
    col.markdown(f"""
<div class="m-card">
  <div class="m-label">{lbl}</div>
  <div class="m-value">{val}<span class="m-unit"> {unit}</span></div>
  <div class="m-badge {bcls}">{badge}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# constraint detail + risk profile
dc1, dc2 = st.columns(2)

with dc1:
    wx_w = {"safety": "^1.3 — storm penalty amplified",
            "fuel":   "×0.8 — moderate tolerance",
            "speed":  "×0.4 — mostly ignored"}[sel_mode]
    pi_w = "15× (strong avoidance)" if sel_mode == "safety" else "8× (moderate avoidance)"
    cur  = "0.85–0.92× discount (Agulhas / monsoon)" if sel_mode == "fuel" else "Not applied"
    fc   = f"Active — 2× westward penalty" if (sel_mode == "fuel" and fuel_pct < 40) else "Inactive"

    st.markdown(f"""
<div class="detail-card">
  <h4>Active Constraints — {sel_meta['icon']} {sel_meta['label']}</h4>
  <div class="d-row"><span class="d-key">Weather penalty</span>   <span class="d-val">{wx_w}</span></div>
  <div class="d-row"><span class="d-key">Piracy zones</span>      <span class="d-val">{pi_w}</span></div>
  <div class="d-row"><span class="d-key">Marine reserves</span>   <span class="d-val">Up to 5× (all modes)</span></div>
  <div class="d-row"><span class="d-key">Ocean currents</span>    <span class="d-val">{cur}</span></div>
  <div class="d-row"><span class="d-key">Fuel-critical routing</span><span class="d-val">{fc}</span></div>
  <div class="d-row"><span class="d-key">Obstacle avoidance</span><span class="d-val">{'Active — ' + str(obs_radius) + ' NM blocked' if obstacle_active else 'Not simulated'}</span></div>
</div>""", unsafe_allow_html=True)

with dc2:
    chips_map = {
        "safety": [("chip-red","Weather ^1.3"),("chip-red","Piracy 15×"),("chip-teal","Marine 5×"),("chip-blue","Safety mode")],
        "fuel":   [("chip-amber","Weather ×0.8"),("chip-teal","Currents 0.88×"),("chip-teal","Marine 5×"),("chip-blue","Piracy 8×")],
        "speed":  [("chip-blue","Weather ×0.4"),("chip-blue","Direct path"),("chip-teal","Marine 5×"),("chip-amber","Piracy 8×")],
    }
    chips = chips_map[sel_mode][:]
    if fuel_pct < 40:     chips.append(("chip-red",   "Fuel critical 2×"))
    if obstacle_active:   chips.append(("chip-amber",  f"Storm {obs_radius}NM"))

    chips_html = "".join(f'<span class="chip {c}">{t}</span>' for c, t in chips)
    max_wi     = sel_stats.get("max_weather_index", 0)
    risk_c     = "#f87171" if max_wi > 10 else "#fbbf24" if max_wi > 5 else "#34d399"
    risk_lbl   = "High risk" if max_wi > 10 else "Moderate" if max_wi > 5 else "Clear"
    co2        = round(sel_stats.get("est_fuel_tons", 0) * 3.17, 1)

    st.markdown(f"""
<div class="detail-card">
  <h4>Route Risk Profile</h4>
  <div class="d-row"><span class="d-key">Max weather index</span>
    <span class="d-val" style="color:{risk_c}">{max_wi:.1f} — {risk_lbl}</span></div>
  <div class="d-row"><span class="d-key">CO₂ estimate</span>
    <span class="d-val">{co2} kg</span></div>
  <div class="d-row"><span class="d-key">Cost chips</span><span class="d-val"></span></div>
  <div style="margin-top:6px">{chips_html}</div>
  <div style="margin-top:14px;font-size:11px;line-height:2">
    <span class="legend-dot" style="background:#1D9E75"></span>Safety — solid, thick if selected<br>
    <span class="legend-dot" style="background:#f59e0b"></span>Fuel — dashed when not selected<br>
    <span class="legend-dot" style="background:#3b82f6"></span>Speed — dashed when not selected
  </div>
</div>""", unsafe_allow_html=True)

# ── QUICK COMPARISON TABLE (all 3 paths) ─────────────────────
st.markdown('<div class="sec-hdr" style="margin-top:20px">All paths — quick comparison</div>',
            unsafe_allow_html=True)

avail      = [mk for mk in ["safety","fuel","speed"] if mk in all_stats]
best_dist  = min(avail, key=lambda k: all_stats[k].get("distance_nm", 99999))
best_time  = min(avail, key=lambda k: all_stats[k].get("est_hours",   99999))
best_fuel  = min(avail, key=lambda k: all_stats[k].get("est_fuel_tons",99999))
best_wx    = min(avail, key=lambda k: all_stats[k].get("avg_weather_index",99999))

rows = []
for mk in ["safety","fuel","speed"]:
    if mk not in all_stats: continue
    s    = all_stats[mk]
    meta = MODE_META[mk]
    co2  = round(s.get("est_fuel_tons", 0) * 3.17, 1)

    def cell(val, best_key, fmt):
        cls = ' class="best-val"' if mk == best_key else ""
        badge = " ✓" if mk == best_key else ""
        return f"<td{cls}>{fmt(val)}{badge}</td>"

    sel_indicator = "★ " if mk == sel_mode else ""
    rows.append(
        f"<tr>"
        f"<td><b style='color:{meta['color']}'>{meta['icon']} {sel_indicator}{meta['label']}</b></td>"
        + cell(s.get("distance_nm",0),    best_dist, lambda v: f"{v:.0f} NM")
        + cell(s.get("est_hours",0),      best_time, lambda v: f"{v:.0f} hrs")
        + cell(s.get("est_fuel_tons",0),  best_fuel, lambda v: f"{v:.1f} t")
        + f"<td>{co2} kg</td>"
        + cell(s.get("avg_weather_index",0), best_wx, lambda v: f"{v:.2f}")
        + f"</tr>"
    )

st.markdown(f"""
<table class="path-cmp">
<thead><tr>
  <th>Path</th><th>Distance</th><th>Duration</th>
  <th>Fuel</th><th>CO₂</th><th>Avg weather</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
<p style="font-size:11px;color:#3a6080;margin-top:5px">
  <span style="color:#34d399;font-weight:700">Green ✓</span> = best in column
  &nbsp;·&nbsp; ★ = currently selected path
</p>""", unsafe_allow_html=True)

# ── replanning log ────────────────────────────────────────────
if st.session_state.replan_log:
    st.markdown('<div class="sec-hdr">Replanning log</div>', unsafe_allow_html=True)
    for ev in reversed(st.session_state.replan_log[-3:]):
        dot = "#f59e0b" if ev["level"] == "warn" else "#34d399"
        st.markdown(f"""
<div style="display:flex;gap:10px;padding:6px 0;border-bottom:1px solid #112240;font-size:12px">
  <div style="width:8px;height:8px;border-radius:50%;background:{dot};margin-top:4px;flex-shrink:0"></div>
  <div><span style="color:#3a6080;font-size:10px">{ev['ts']}</span><br>
  <span style="color:#a8c0d8">{ev['msg']}</span></div>
</div>""", unsafe_allow_html=True)

# ── bottom nav ────────────────────────────────────────────────
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
nb1, nb2, nb3 = st.columns([1, 3, 1])
with nb1:
    if st.button("← Back to Constraints", use_container_width=True):
        st.switch_page("pages/2_Constraints_Overview.py")
with nb3:
    if st.button("→ View Summary & Export", type="primary", use_container_width=True):
        st.switch_page("pages/4_Summary.py")
