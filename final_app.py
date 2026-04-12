"""
final_app.py
=============
Indian Ocean Strategic Ship Routing System
Group 13 | Industrial Decision Support System
"""

import streamlit as st
from streamlit_folium import st_folium
import folium
import numpy as np
from global_land_mask import globe
from scipy.spatial import KDTree
import heapq

# ─────────────────────────────────────────────────────────────
#  1. PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Maritime DSS | Group 13",
    page_icon="🚢",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────
#  2. CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1a3a5c;
        border-bottom: 3px solid #1a7fc1;
        padding-bottom: 0.3rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.85rem;
        color: #6b8fa8;
        letter-spacing: 0.08em;
        margin-bottom: 1.5rem;
    }
    .metric-box {
        background: #0d2137;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        border-left: 4px solid #1a7fc1;
        color: white;
    }
    .metric-box.green  { border-left-color: #00c97a; }
    .metric-box.amber  { border-left-color: #f5a623; }
    .metric-box.red    { border-left-color: #e74c3c; }
    .metric-label {
        font-size: 0.7rem;
        letter-spacing: 0.14em;
        color: #7fb3d3;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.1;
    }
    .metric-unit {
        font-size: 0.75rem;
        color: #7fb3d3;
    }
    .grade-badge {
        display: inline-block;
        padding: 0.2rem 0.9rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.2rem;
    }
    .grade-A { background:#d4f5e9; color:#0a6644; }
    .grade-B { background:#d4eaff; color:#0a3566; }
    .grade-C { background:#fff3d4; color:#7a5500; }
    .grade-D { background:#ffd4d4; color:#7a0000; }
    .info-box {
        background: #eaf4ff;
        border-left: 3px solid #1a7fc1;
        border-radius: 6px;
        padding: 0.6rem 0.9rem;
        font-size: 0.83rem;
        color: #0d2137;
        margin-top: 0.4rem;
    }
    .section-head {
        font-size: 0.75rem;
        letter-spacing: 0.16em;
        color: #1a7fc1;
        text-transform: uppercase;
        border-bottom: 1px solid #c8dff0;
        padding-bottom: 0.3rem;
        margin: 1.2rem 0 0.7rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  3. PORT DATABASE
# ─────────────────────────────────────────────────────────────
PORTS = {
    "Mumbai":                  [18.9252,  72.8344],
    "Chennai":                 [13.0827,  80.2707],
    "Kolkata":                 [22.5726,  88.3639],
    "Cochin (Kochi)":          [ 9.9312,  76.2673],
    "Jawaharlal Nehru Port":   [18.9480,  72.9530],
    "Visakhapatnam":           [17.6868,  83.2185],
    "Kandla":                  [23.0333,  70.2167],
    "Colombo":                 [ 6.9271,  79.8612],
    "Hambantota":              [ 6.1241,  81.1185],
    "Chittagong":              [22.3475,  91.8123],
    "Karachi":                 [24.8607,  67.0011],
    "Gwadar":                  [25.1216,  62.3254],
    "Dubai (Jebel Ali)":       [24.9857,  55.0272],
    "Abu Dhabi":               [24.7136,  54.4008],
    "Muscat":                  [23.5880,  58.3829],
    "Aden":                    [12.7855,  44.9936],
    "Djibouti":                [11.5720,  43.1450],
    "Mombasa":                 [-4.0435,  39.6682],
    "Dar es Salaam":           [-6.7924,  39.2083],
    "Durban":                  [-29.8587, 31.0218],
    "Port Louis (Mauritius)":  [-20.1619, 57.4989],
    "Toamasina (Madagascar)":  [-18.1443, 49.4012],
    "Singapore":               [ 1.3521, 103.8198],
    "Port Klang (Malaysia)":   [ 3.0319, 101.3853],
    "Jakarta":                 [-6.1044, 106.8294],
    "Fremantle (Perth)":       [-32.0569, 115.7436],
    "Port Hedland":            [-20.3100, 118.5774],
}

PORT_NAMES = sorted(PORTS.keys())

# ─────────────────────────────────────────────────────────────
#  4. VESSEL PROFILES
# ─────────────────────────────────────────────────────────────
VESSELS = {
    "Container Carrier":  {"speed": 20.0, "fuel_day": 120.0},
    "Oil Tanker (VLCC)":  {"speed": 15.0, "fuel_day":  80.0},
    "Bulk Carrier":       {"speed": 14.0, "fuel_day":  45.0},
    "LNG Carrier":        {"speed": 19.5, "fuel_day": 110.0},
    "General Cargo":      {"speed": 13.0, "fuel_day":  30.0},
}

# ─────────────────────────────────────────────────────────────
#  5. RISK ZONES
# ─────────────────────────────────────────────────────────────
RISK_ZONES = [
    # (lat_min, lat_max, lon_min, lon_max, score, label, color)
    (  5,  15,  45,  58, 18.0, "Piracy — Gulf of Aden",      "red"   ),
    (-18, -10,  35,  42,  8.0, "Piracy — Mozambique Channel", "red"   ),
    ( -5,  10,  65,  88, 15.0, "Cyclone — Bay of Bengal",     "orange"),
    (  5,  20,  55,  72, 10.0, "Cyclone — Arabian Sea",       "orange"),
    (  1,  12,  71,  74,  6.0, "Reef — Maldives",             "purple"),
    (  1,   6,  99, 105,  5.0, "High Traffic — Malacca",      "blue"  ),
]

def get_risk(lat, lon):
    max_risk = 0.0
    for z in RISK_ZONES:
        if z[0] <= lat <= z[1] and z[2] <= lon <= z[3]:
            if z[4] > max_risk:
                max_risk = z[4]
    return max_risk

# ─────────────────────────────────────────────────────────────
#  6. GRID  (cached so it only builds once)
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🌊 Building Indian Ocean navigation mesh...")
def build_grid():
    nodes = []
    for lat in np.arange(-40, 30, 2.5):
        for lon in np.arange(25, 115, 2.5):
            if not globe.is_land(lat, lon):
                nodes.append([lat, lon])
    nodes = np.array(nodes)
    tree  = KDTree(nodes)
    graph = {i: [n for n in tree.query_ball_point(p, r=3.9) if n != i]
             for i, p in enumerate(nodes)}
    return nodes, tree, graph

nodes, tree, graph = build_grid()

# ─────────────────────────────────────────────────────────────
#  7. DISTANCE UTILITY
# ─────────────────────────────────────────────────────────────
def haversine_nm(p1, p2):
    lat1, lon1, lat2, lon2 = map(np.radians, [p1[0], p1[1], p2[0], p2[1]])
    a = (np.sin((lat2-lat1)/2)**2
         + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2)
    return 2 * 3440.065 * np.arcsin(np.sqrt(a))

# ─────────────────────────────────────────────────────────────
#  8. HEADER
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🚢 Indian Ocean Strategic Ship Routing System</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-title">INDUSTRIAL DECISION SUPPORT SYSTEM &nbsp;|&nbsp; GROUP 13</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  9. SIDEBAR
# ─────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Voyage Parameters")

# Vessel
vessel_name = st.sidebar.selectbox("🛳️ Vessel Type", list(VESSELS.keys()))
v = VESSELS[vessel_name]
st.sidebar.markdown(
    f'<div class="info-box">Speed: <b>{v["speed"]} kts</b> &nbsp;|&nbsp; '
    f'Fuel: <b>{v["fuel_day"]} MT/day</b></div>',
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# Ports
origin_name = st.sidebar.selectbox(
    "🟢 Departure Port", PORT_NAMES,
    index=PORT_NAMES.index("Mumbai")
)
dest_name = st.sidebar.selectbox(
    "🔴 Arrival Port", PORT_NAMES,
    index=PORT_NAMES.index("Port Louis (Mauritius)")
)

# Custom coordinates toggle
use_custom = st.sidebar.checkbox("✏️ Use custom coordinates instead")
if use_custom:
    c_origin = st.sidebar.text_input("Origin (lat, lon)", "18.9, 72.8")
    c_dest   = st.sidebar.text_input("Destination (lat, lon)", "-20.1, 57.5")
    try:
        origin_coords = [float(x.strip()) for x in c_origin.split(",")]
        dest_coords   = [float(x.strip()) for x in c_dest.split(",")]
        origin_label  = f"Custom ({origin_coords[0]}, {origin_coords[1]})"
        dest_label    = f"Custom ({dest_coords[0]}, {dest_coords[1]})"
    except Exception:
        st.sidebar.error("Invalid coordinates!")
        origin_coords = PORTS["Mumbai"]
        dest_coords   = PORTS["Port Louis (Mauritius)"]
        origin_label  = "Mumbai"
        dest_label    = "Port Louis (Mauritius)"
else:
    origin_coords = PORTS[origin_name]
    dest_coords   = PORTS[dest_name]
    origin_label  = origin_name
    dest_label    = dest_name

st.sidebar.markdown("---")

# Strategy
STRATEGY_INFO = {
    "Economy (Shortest)":  {"risk_scale": 1,   "desc": "Shortest path, ignores hazards"},
    "Minimum Fuel":        {"risk_scale": 8,   "desc": "Optimized for lowest fuel burn"},
    "Standard (Balanced)": {"risk_scale": 25,  "desc": "Balance of time, fuel & safety"},
    "Maximum Safety":      {"risk_scale": 80,  "desc": "Aggressively avoids risk zones"},
    "Storm Avoidance":     {"risk_scale": 180, "desc": "Hard avoidance of storm corridors"},
}
strategy_name = st.sidebar.selectbox("🎯 Optimization Strategy", list(STRATEGY_INFO.keys()), index=2)
st.sidebar.markdown(
    f'<div class="info-box">💡 {STRATEGY_INFO[strategy_name]["desc"]}</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# Map options
show_zones  = st.sidebar.checkbox("Show Risk Zones on Map", value=True)
show_ports  = st.sidebar.checkbox("Show All Ports on Map",  value=True)

run_btn = st.sidebar.button("⚙️ Execute Optimization", use_container_width=True)

# ─────────────────────────────────────────────────────────────
#  10. SESSION STATE
# ─────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None

# ─────────────────────────────────────────────────────────────
#  11. OPTIMIZATION LOGIC
# ─────────────────────────────────────────────────────────────
if run_btn:
    if origin_coords == dest_coords:
        st.error("Departure and Arrival ports cannot be the same!")
    else:
        with st.spinner("🔄 Running A* multi-objective optimization..."):
            try:
                s_idx = int(tree.query(origin_coords)[1])
                e_idx = int(tree.query(dest_coords)[1])
                risk_scale = STRATEGY_INFO[strategy_name]["risk_scale"]

                pq      = [(0.0, s_idx, [s_idx])]
                best_g  = {}

                while pq:
                    cost, curr, path = heapq.heappop(pq)

                    if curr in best_g and best_g[curr] <= cost:
                        continue
                    best_g[curr] = cost

                    if curr == e_idx:
                        # ── Compute metrics ──────────────────
                        dist_nm = sum(
                            haversine_nm(nodes[path[i]], nodes[path[i+1]])
                            for i in range(len(path)-1)
                        )
                        risks = [get_risk(nodes[i][0], nodes[i][1]) for i in path]
                        avg_risk = float(np.mean(risks))

                        speed_factor   = max(0.7, 1.0 - avg_risk * 0.02)
                        eff_speed      = v["speed"] * speed_factor
                        voyage_days    = dist_nm / (eff_speed * 24.0)
                        fuel_mt        = voyage_days * v["fuel_day"]
                        co2_mt         = fuel_mt * 3.17
                        fuel_cost_usd  = fuel_mt * 650

                        if avg_risk < 1.0:   grade = "A"
                        elif avg_risk < 5.0: grade = "B"
                        elif avg_risk < 10:  grade = "C"
                        else:                grade = "D"

                        # Great-circle reference
                        gc_nm    = haversine_nm(origin_coords, dest_coords)
                        overhead = ((dist_nm - gc_nm) / gc_nm) * 100

                        st.session_state.result = {
                            "path":        path,
                            "distance":    dist_nm,
                            "days":        voyage_days,
                            "fuel":        fuel_mt,
                            "co2":         co2_mt,
                            "fuel_cost":   fuel_cost_usd,
                            "avg_risk":    avg_risk,
                            "grade":       grade,
                            "gc_nm":       gc_nm,
                            "overhead":    overhead,
                            "origin":      origin_label,
                            "dest":        dest_label,
                            "origin_coords": origin_coords,
                            "dest_coords":   dest_coords,
                        }
                        break

                    for nb in graph.get(curr, []):
                        dist_seg = haversine_nm(nodes[curr], nodes[nb])
                        risk_val = get_risk(nodes[nb][0], nodes[nb][1])
                        penalty  = 1.0 + (risk_val * risk_scale / 20.0)
                        new_g    = cost + dist_seg * penalty
                        if nb not in best_g or best_g[nb] > new_g:
                            h = haversine_nm(nodes[nb], dest_coords)
                            heapq.heappush(pq, (new_g + h, nb, path + [nb]))

                if st.session_state.result is None:
                    st.error("No navigable route found. Try different ports.")

            except Exception as e:
                st.error(f"Error during optimization: {e}")
                import traceback
                st.code(traceback.format_exc())

# ─────────────────────────────────────────────────────────────
#  12. DISPLAY RESULTS
# ─────────────────────────────────────────────────────────────
if st.session_state.result:
    res = st.session_state.result

    # ── KPI CARDS ─────────────────────────────────────────────
    st.markdown('<div class="section-head">▶ ROUTE PERFORMANCE SUMMARY</div>',
                unsafe_allow_html=True)

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    def kpi(col, label, value, unit, color=""):
        col.markdown(f"""
        <div class="metric-box {color}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-unit">{unit}</div>
        </div>""", unsafe_allow_html=True)

    kpi(k1, "Total Distance",    f"{res['distance']:,.0f}", "Nautical Miles")
    kpi(k2, "Voyage Time",       f"{res['days']:.1f}",      "Days at Sea",    "green")
    kpi(k3, "Fuel Consumption",  f"{res['fuel']:,.0f}",     "Metric Tons",    "amber")
    kpi(k4, "CO₂ Emissions",     f"{res['co2']:,.0f}",      "MT CO₂",         "amber")
    kpi(k5, "Est. Fuel Cost",    f"${res['fuel_cost']:,.0f}","USD",            "amber")

    grade_color = {"A": "green", "B": "", "C": "amber", "D": "red"}[res["grade"]]
    k6.markdown(f"""
    <div class="metric-box {grade_color}">
        <div class="metric-label">Safety Grade</div>
        <div style="margin-top:0.4rem">
            <span class="grade-badge grade-{res['grade']}">Grade {res['grade']}</span>
        </div>
        <div class="metric-unit">Avg risk: {res['avg_risk']:.2f}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── MAP ───────────────────────────────────────────────────
    st.markdown('<div class="section-head">▶ OPTIMIZED ROUTE MAP</div>',
                unsafe_allow_html=True)

    center_lat = (res["origin_coords"][0] + res["dest_coords"][0]) / 2
    center_lon = (res["origin_coords"][1] + res["dest_coords"][1]) / 2

    m = folium.Map(location=[center_lat, center_lon],
                   zoom_start=4, tiles="CartoDB positron")

    # Risk zones
    if show_zones:
        zone_colors = {"red": "red", "orange": "orange",
                       "purple": "purple", "blue": "blue"}
        for z in RISK_ZONES:
            folium.Rectangle(
                bounds=[[z[0], z[2]], [z[1], z[3]]],
                color=z[6], fill=True, fill_opacity=0.12,
                weight=1.5, tooltip=z[5]
            ).add_to(m)

    # All ports (small dots)
    if show_ports:
        for pname, pcoords in PORTS.items():
            folium.CircleMarker(
                location=pcoords,
                radius=4,
                color="#1a5276",
                fill=True,
                fill_color="#2e86c1",
                fill_opacity=0.75,
                tooltip=pname,
            ).add_to(m)

    # Route line
    route_pts = [nodes[i].tolist() for i in res["path"]]
    folium.PolyLine(route_pts, color="#1a7fc1", weight=5,
                    opacity=0.9, tooltip="Optimized Route").add_to(m)

    # Origin marker — with PORT NAME
    folium.Marker(
        location=res["origin_coords"],
        tooltip=f"🟢 {res['origin']}",
        popup=folium.Popup(
            f"<b>DEPARTURE</b><br>{res['origin']}<br>"
            f"Lat: {res['origin_coords'][0]:.3f}°<br>"
            f"Lon: {res['origin_coords'][1]:.3f}°",
            max_width=200
        ),
        icon=folium.Icon(color="green", icon="ship", prefix="fa"),
    ).add_to(m)

    # Destination marker — with PORT NAME
    folium.Marker(
        location=res["dest_coords"],
        tooltip=f"🔴 {res['dest']}",
        popup=folium.Popup(
            f"<b>DESTINATION</b><br>{res['dest']}<br>"
            f"Lat: {res['dest_coords'][0]:.3f}°<br>"
            f"Lon: {res['dest_coords'][1]:.3f}°",
            max_width=200
        ),
        icon=folium.Icon(color="red", icon="anchor", prefix="fa"),
    ).add_to(m)

    st_folium(m, width="100%", height=520, key="main_map")

    # ── ANALYTICS TABS ────────────────────────────────────────
    st.markdown('<div class="section-head">▶ DETAILED ANALYTICS</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Route Profile", "⚠️ Risk Analysis", "⛽ Fuel & Emissions"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Voyage Summary**")
            st.markdown(f"""
            - **Origin:** {res['origin']}
            - **Destination:** {res['dest']}
            - **Strategy:** {strategy_name}
            - **Vessel:** {vessel_name} @ {v['speed']} kts
            - **Distance:** {res['distance']:,.1f} NM
            - **Voyage Time:** {res['days']:.2f} days ({res['days']*24:.0f} hours)
            - **Waypoints:** {len(res['path'])}
            """)
        with col2:
            st.markdown("**Great-Circle vs Optimized**")
            st.info(
                f"📏 Great-circle (shortest possible): **{res['gc_nm']:,.1f} NM**\n\n"
                f"🗺️ Optimized route: **{res['distance']:,.1f} NM**\n\n"
                f"📈 Route overhead: **+{res['overhead']:.1f}%** "
                f"(added for safety/strategy)"
            )

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Risk Summary**")
            grade_desc = {"A": "✅ Open ocean — no hazards",
                          "B": "🟡 Minor risk exposure",
                          "C": "🟠 Moderate risk zones crossed",
                          "D": "🔴 High risk route"}
            st.markdown(f"""
            - **Average Risk Score:** {res['avg_risk']:.3f}
            - **Safety Grade:** Grade {res['grade']} — {grade_desc[res['grade']]}
            """)
        with c2:
            st.markdown("**Risk Zones in Region**")
            for z in RISK_ZONES:
                st.markdown(f"🔸 **{z[5]}** — Risk score: {z[4]}")

    with tab3:
        c1, c2, c3 = st.columns(3)
        c1.metric("Fuel Consumed",  f"{res['fuel']:,.1f} MT")
        c2.metric("CO₂ Emitted",    f"{res['co2']:,.1f} MT")
        c3.metric("Fuel Cost (est)",f"${res['fuel_cost']:,.0f}")
        st.markdown(f"""
        ---
        - **Fuel per 1,000 NM:** {res['fuel']/res['distance']*1000:.1f} MT
        - **CO₂ per 1,000 NM:** {res['co2']/res['distance']*1000:.1f} MT
        - **Vessel base consumption:** {v['fuel_day']} MT/day at {v['speed']} kts
        - **Bunker price assumed:** $650 / MT
        """)

# ─────────────────────────────────────────────────────────────
#  13. IDLE STATE  (before optimization runs)
# ─────────────────────────────────────────────────────────────
else:
    st.markdown('<div class="section-head">▶ SYSTEM READY</div>', unsafe_allow_html=True)

    # Base map with all ports + risk zones
    m = folium.Map(location=[8, 72], zoom_start=4, tiles="CartoDB positron")

    for z in RISK_ZONES:
        folium.Rectangle(
            bounds=[[z[0], z[2]], [z[1], z[3]]],
            color=z[6], fill=True, fill_opacity=0.12,
            weight=1.5, tooltip=z[5]
        ).add_to(m)

    for pname, pcoords in PORTS.items():
        folium.CircleMarker(
            location=pcoords,
            radius=5,
            color="#1a5276",
            fill=True,
            fill_color="#2e86c1",
            fill_opacity=0.8,
            tooltip=pname,
        ).add_to(m)

    st_folium(m, width="100%", height=480, key="idle_map")

    st.info("🚢 Select ports and strategy in the sidebar, then click **Execute Optimization**.")

    col1, col2, col3 = st.columns(3)
    col1.markdown("""**🛰️ Algorithm**
- Multi-objective A* search
- Haversine great-circle distance
- Configurable risk penalty scales
- Admissible heuristic function""")
    col2.markdown("""**⚠️ Risk Zones Modelled**
- Piracy: Gulf of Aden, Mozambique
- Cyclone: Bay of Bengal, Arabian Sea
- Reef: Maldives / Lakshadweep
- Traffic: Strait of Malacca""")
    col3.markdown("""**📊 What You Get**
- Optimized waypoint route
- Fuel & CO₂ estimates
- Safety grade (A to D)
- Voyage time & distance
- Great-circle comparison""")

# ─────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center><small>Indian Ocean Maritime Route Optimization DSS &nbsp;|&nbsp; "
    "Group 13 &nbsp;|&nbsp; Python · Streamlit · NumPy · SciPy · Folium</small></center>",
    unsafe_allow_html=True
)