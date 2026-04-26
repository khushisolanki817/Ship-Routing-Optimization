"""
pages/4_Summary.py  —  Comparison & Summary (UPDATED)
=======================================================
✅ Concise, professional summary — no verbose paragraphs
✅ 3 path cards with key stats
✅ Best-value highlighted in green
✅ Smart recommendation (1 line, context-aware)
✅ Compact comparison table
✅ Bar chart comparison (no external libs)
✅ CSV + TXT export
✅ Event log
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Maritime DSS — Summary",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if not st.session_state.get("authenticated"):
    st.switch_page("Login.py")

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
[data-baseweb="select"] > div { background-color:#0c1e38 !important; border-color:#1e3a5f !important; border-radius:8px !important; }
[data-baseweb="select"] span, [data-baseweb="select"] div[class*="singleValue"] { color:#c8d8f0 !important; }
[data-baseweb="popover"] ul, [role="listbox"] { background-color:#0c1e38 !important; border:1px solid #1e3a5f !important; }
[role="option"] { background-color:#0c1e38 !important; color:#c8d8f0 !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background-color:#122840 !important; color:#e2ecff !important; }

[data-testid="stAppViewContainer"] { background:#060f1e; }
[data-testid="stSidebar"]          { display:none; }
[data-testid="collapsedControl"]   { display:none; }
section[data-testid="stSidebarNav"]{ display:none; }
* { color:#c8d8f0; }
h1,h2,h3 { color:#e2ecff !important; }

.topnav { display:flex;align-items:center;justify-content:space-between;background:#08152a;border-bottom:1px solid #112240;padding:10px 24px;margin:-1rem -1rem 1.5rem; }
.nav-logo { font-size:18px;font-weight:700;color:#e2ecff; }
.nav-steps { display:flex; }
.step { padding:6px 20px;font-size:12px;font-weight:500;color:#3a6080;border-bottom:2px solid transparent; }
.step.done { color:#1D9E75;border-color:#1D9E75; }
.step.active { color:#e2ecff;border-color:#3b82f6; }
.nav-user { font-size:12px;color:#3a6080;background:#0c1e38;border:1px solid #1a3050;border-radius:20px;padding:4px 12px; }

/* Path cards */
.path-card { background:#0a1a30;border:1.5px solid #1a3050;border-radius:12px;padding:18px 16px;position:relative;height:100%; }
.path-card.rec { border-color:#1D9E75; }
.rec-badge { position:absolute;top:-10px;left:50%;transform:translateX(-50%);background:#1D9E75;color:#fff;font-size:10px;font-weight:700;padding:3px 12px;border-radius:10px;white-space:nowrap; }
.path-icon { font-size:28px;margin-bottom:6px; }
.path-name { font-size:15px;font-weight:700;margin-bottom:2px; }
.path-sub  { font-size:11px;color:#5a7fa8;margin-bottom:12px; }
.s-row     { display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #112240;font-size:12px; }
.s-row:last-child { border-bottom:none; }
.s-key { color:#5a7fa8; }
.s-val { color:#e2ecff;font-weight:600; }
.s-best{ color:#34d399;font-weight:700; }

/* Comparison table */
.cmp-table { width:100%;border-collapse:collapse;font-size:12px; }
.cmp-table th { background:#0c1e38;color:#5a7fa8;font-weight:600;text-transform:uppercase;letter-spacing:.05em;padding:9px 14px;border-bottom:1px solid #1a3050;white-space:nowrap; }
.cmp-table td { padding:9px 14px;border-bottom:1px solid #112240;color:#a8c0d8; }
.cmp-table tr:hover td { background:#0a1a30; }
.best-cell { color:#34d399 !important;font-weight:700 !important; }

/* Recommendation */
.rec-strip { display:flex;align-items:center;gap:14px;background:#081f18;border:1px solid #1D9E75;border-radius:10px;padding:14px 18px;margin:14px 0; }
.rec-icon  { font-size:28px;flex-shrink:0; }
.rec-label { font-size:13px;font-weight:700;color:#34d399;margin-bottom:2px; }
.rec-text  { font-size:12px;color:#7abfa0;line-height:1.5; }
.rec-stats { display:flex;gap:16px;flex-shrink:0; }
.rec-stat  { text-align:center; }
.rs-val    { font-size:16px;font-weight:700;color:#e2ecff; }
.rs-lbl    { font-size:10px;color:#3a6080;text-transform:uppercase; }

/* Bar chart */
.bar-wrap  { background:#08152a;border:1px solid #1a3050;border-radius:10px;padding:14px 16px; }
.bar-label { font-size:10px;color:#5a7fa8;text-transform:uppercase;font-weight:600;margin-bottom:10px; }
.bar-item  { margin-bottom:8px; }
.bar-top   { display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px; }
.bar-track { background:#1a3050;height:7px;border-radius:4px;overflow:hidden; }
.bar-fill  { height:100%;border-radius:4px; }

.sec-hdr { font-size:11px;font-weight:700;color:#3a6080;text-transform:uppercase;letter-spacing:.08em;margin:20px 0 10px; }
</style>
""", unsafe_allow_html=True)

MODE_META = {
    "safety": {"label":"Safety First",   "icon":"🛡️", "sub":"Storm & piracy avoidance",   "color":"#1D9E75"},
    "fuel":   {"label":"Fuel Efficient",  "icon":"⛽",  "sub":"Ocean current optimised",    "color":"#f59e0b"},
    "speed":  {"label":"Max Speed",       "icon":"⚡",  "sub":"Shortest great-circle path", "color":"#3b82f6"},
}

def douglas_peucker(points, epsilon=0.3):
    if len(points) < 3: return points
    dmax, idx = 0.0, 0
    start, end = np.array(points[0]), np.array(points[-1])
    line = end - start; norm = np.linalg.norm(line)
    for i in range(1, len(points)-1):
        d = (np.linalg.norm(np.cross(line, start-np.array(points[i])))/norm
             if norm>0 else np.linalg.norm(np.array(points[i])-start))
        if d > dmax: dmax, idx = d, i
    if dmax > epsilon:
        return douglas_peucker(points[:idx+1],epsilon)[:-1]+douglas_peucker(points[idx:],epsilon)
    return [points[0], points[-1]]

# ── top nav ──────────────────────────────────────────────────
uname = st.session_state.get("username","user")
urole = st.session_state.get("user_role","Officer")
st.markdown(f"""
<div class="topnav">
  <div class="nav-logo">🚢 Maritime DSS</div>
  <div class="nav-steps">
    <div class="step done">① Login</div>
    <div class="step done">② Constraints</div>
    <div class="step done">③ Route Map</div>
    <div class="step active">④ Summary</div>
  </div>
  <div class="nav-user">👤 {uname} · {urole}</div>
</div>
""", unsafe_allow_html=True)

_lc, _rc = st.columns([6, 1])
with _rc:
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        for k in ["authenticated","username","all_routes","all_stats","route_params","replan_log","route_calculated"]:
            st.session_state[k] = False if k=="authenticated" else ({} if k in ["all_routes","all_stats","route_params"] else ([] if k=="replan_log" else ("" if k=="username" else False)))
        st.switch_page("Login.py")

# ── data ─────────────────────────────────────────────────────
all_routes = st.session_state.get("all_routes", {})
all_stats  = st.session_state.get("all_stats",  {})
params     = st.session_state.get("route_params", {})

if not all_routes or not params:
    st.warning("No route data. Please calculate routes first.")
    if st.button("← Go to Constraints"):
        st.switch_page("pages/2_Constraints_Overview.py")
    st.stop()

start_p   = params["start_p"]
end_p     = params["end_p"]
ship_type = params["ship_type"]
fuel_pct  = params["fuel_pct"]
obs_active= params.get("obstacle_active", False)

avail      = [mk for mk in ["safety","fuel","speed"] if mk in all_stats]
best_dist  = min(avail, key=lambda k: all_stats[k].get("distance_nm",99999))
best_time  = min(avail, key=lambda k: all_stats[k].get("est_hours",99999))
best_fuel  = min(avail, key=lambda k: all_stats[k].get("est_fuel_tons",99999))
best_wx    = min(avail, key=lambda k: all_stats[k].get("avg_weather_index",99999))

# Smart recommendation (context-aware, one line)
if fuel_pct < 35:
    recommended = "fuel"
    rec_reason  = f"Fuel critical ({fuel_pct}%) — fuel-efficient routing minimises consumption."
elif obs_active:
    recommended = "safety"
    rec_reason  = "Storm detected — safety route provides maximum obstacle clearance."
else:
    scores = {mk: (all_stats[mk].get("est_hours",999)/200 * 0.4
                   + all_stats[mk].get("est_fuel_tons",999)/50 * 0.3
                   + all_stats[mk].get("avg_weather_index",1)/5 * 0.3)
              for mk in avail}
    recommended = min(scores, key=lambda k: scores[k])
    rec_reason  = "Best overall balance of time, fuel, and weather for this voyage."

# ── header ───────────────────────────────────────────────────
st.markdown("<h2 style='margin:0 0 2px'>Voyage Summary</h2>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:#3a6080;font-size:13px;margin:0 0 16px'>"
    f"{start_p} → {end_p} · {ship_type} · Fuel {fuel_pct}%</p>",
    unsafe_allow_html=True
)

# ── RECOMMENDATION STRIP ──────────────────────────────────────
rec_meta  = MODE_META[recommended]
rec_s     = all_stats[recommended]
co2_rec   = round(rec_s.get("est_fuel_tons",0)*3.17, 1)

st.markdown(f"""
<div class="rec-strip">
  <div class="rec-icon">{rec_meta['icon']}</div>
  <div style="flex:1">
    <div class="rec-label">Recommended: {rec_meta['label']}</div>
    <div class="rec-text">{rec_reason}</div>
  </div>
  <div class="rec-stats">
    <div class="rec-stat"><div class="rs-val">{rec_s.get('distance_nm',0):.0f}</div><div class="rs-lbl">NM</div></div>
    <div class="rec-stat"><div class="rs-val">{rec_s.get('est_hours',0):.0f}</div><div class="rs-lbl">hrs</div></div>
    <div class="rec-stat"><div class="rs-val">{rec_s.get('est_fuel_tons',0):.1f}</div><div class="rs-lbl">t fuel</div></div>
    <div class="rec-stat"><div class="rs-val">{co2_rec}</div><div class="rs-lbl">kg CO₂</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── PATH CARDS ────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">Path comparison</div>', unsafe_allow_html=True)
card_cols = st.columns(3)

for col, mk in zip(card_cols, ["safety","fuel","speed"]):
    if mk not in all_stats: continue
    s      = all_stats[mk]
    meta   = MODE_META[mk]
    is_rec = (mk == recommended)
    co2    = round(s.get("est_fuel_tons",0)*3.17, 1)
    wx     = s.get("avg_weather_index",0)
    wx_c   = "#34d399" if wx<3 else "#fbbf24" if wx<6 else "#f87171"
    wx_lbl = "Clear" if wx<3 else "Moderate" if wx<6 else "Rough"

    def sv(key, best_key):
        return "s-best" if mk == best_key else "s-val"

    rec_html = '<div class="rec-badge">★ Recommended</div>' if is_rec else ""
    rec_cls  = "rec" if is_rec else ""

    col.markdown(f"""
<div class="path-card {rec_cls}">
  {rec_html}
  <div class="path-icon">{meta['icon']}</div>
  <div class="path-name" style="color:{meta['color']}">{meta['label']}</div>
  <div class="path-sub">{meta['sub']}</div>

  <div class="s-row">
    <span class="s-key">Distance</span>
    <span class="{sv('d',best_dist)}">{s.get('distance_nm',0):.0f} NM</span>
  </div>
  <div class="s-row">
    <span class="s-key">Duration</span>
    <span class="{sv('t',best_time)}">{s.get('est_hours',0):.0f} hrs · {s.get('est_days',0):.1f}d</span>
  </div>
  <div class="s-row">
    <span class="s-key">Speed</span>
    <span class="s-val">{s.get('speed_knots',0)} kts</span>
  </div>
  <div class="s-row">
    <span class="s-key">Fuel</span>
    <span class="{sv('f',best_fuel)}">{s.get('est_fuel_tons',0):.1f} t</span>
  </div>
  <div class="s-row">
    <span class="s-key">CO₂</span>
    <span class="s-val">{co2} kg</span>
  </div>
  <div class="s-row">
    <span class="s-key">Weather</span>
    <span style="color:{wx_c};font-weight:600">{wx_lbl} ({wx:.2f})</span>
  </div>
  <div class="s-row">
    <span class="s-key">Max weather</span>
    <span class="s-val">{s.get('max_weather_index',0):.2f}</span>
  </div>
  <div class="s-row">
    <span class="s-key">Waypoints</span>
    <span class="s-val">{s.get('waypoints',0)}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── COMPARISON TABLE ──────────────────────────────────────────
st.markdown('<div class="sec-hdr">Full comparison table</div>', unsafe_allow_html=True)

def bval(mk, key, best_key, fmt):
    v   = all_stats.get(mk,{}).get(key,0)
    cls = ' class="best-cell"' if mk==best_key else ""
    return f'<td{cls}>{fmt(v)}{"✓" if mk==best_key else ""}</td>'

rows_html = []
for mk in ["safety","fuel","speed"]:
    if mk not in all_stats: continue
    meta = MODE_META[mk]
    s    = all_stats[mk]
    co2  = round(s.get("est_fuel_tons",0)*3.17,1)
    rows_html.append(
        f'<tr>'
        f'<td><b style="color:{meta["color"]}">{meta["icon"]} {meta["label"]}</b>'
        f'{"&nbsp;<span style=\'background:#083d20;color:#34d399;font-size:10px;padding:1px 6px;border-radius:6px\'>REC</span>" if mk==recommended else ""}</td>'
        + bval(mk,"distance_nm",    best_dist, lambda v: f"{v:.0f} NM")
        + bval(mk,"est_hours",      best_time, lambda v: f"{v:.0f} h / {all_stats.get(mk,{}).get('est_days',0):.1f}d")
        + bval(mk,"speed_knots",    best_time, lambda v: f"{v} kts")
        + bval(mk,"est_fuel_tons",  best_fuel, lambda v: f"{v:.1f} t")
        + f'<td>{co2} kg</td>'
        + bval(mk,"avg_weather_index", best_wx, lambda v: f"{v:.2f}")
        + bval(mk,"max_weather_index", best_wx, lambda v: f"{v:.2f}")
        + f'<td>{s.get("waypoints",0)}</td>'
        + '</tr>'
    )

st.markdown(f"""
<table class="cmp-table">
<thead><tr>
  <th>Mode</th><th>Distance</th><th>Duration</th><th>Speed</th>
  <th>Fuel</th><th>CO₂</th><th>Avg wx</th><th>Max wx</th><th>WP</th>
</tr></thead>
<tbody>{"".join(rows_html)}</tbody>
</table>
<p style="font-size:11px;color:#3a6080;margin-top:5px">
  <span style="color:#34d399;font-weight:700">Green ✓</span> = best in column
</p>""", unsafe_allow_html=True)

# ── BAR CHART COMPARISON ──────────────────────────────────────
st.markdown('<div class="sec-hdr">Visual comparison</div>', unsafe_allow_html=True)

chart_items = [
    ("Distance (NM)",    "distance_nm",      lambda v: f"{v:.0f}"),
    ("Duration (hrs)",   "est_hours",        lambda v: f"{v:.0f}"),
    ("Fuel (tonnes)",    "est_fuel_tons",    lambda v: f"{v:.1f}"),
    ("Avg weather idx",  "avg_weather_index",lambda v: f"{v:.2f}"),
]

bar_cols = st.columns(4)
for col, (chart_label, key, fmt) in zip(bar_cols, chart_items):
    vals   = {mk: all_stats[mk].get(key,0) for mk in avail}
    max_v  = max(vals.values()) if vals else 1
    bars   = ""
    for mk, v in vals.items():
        meta = MODE_META[mk]
        pct  = int(100 * v / max_v) if max_v > 0 else 0
        bars += (
            f"<div class='bar-item'>"
            f"<div class='bar-top'>"
            f"  <span style='color:{meta['color']}'>{meta['icon']} {meta['label']}</span>"
            f"  <span style='color:#e2ecff;font-weight:600'>{fmt(v)}</span>"
            f"</div>"
            f"<div class='bar-track'>"
            f"  <div class='bar-fill' style='width:{pct}%;background:{meta['color']}'></div>"
            f"</div></div>"
        )
    col.markdown(
        f"<div class='bar-wrap'><div class='bar-label'>{chart_label}</div>{bars}</div>",
        unsafe_allow_html=True
    )

# ── EXPORT ────────────────────────────────────────────────────
st.markdown('<div class="sec-hdr">Export</div>', unsafe_allow_html=True)
exp_cols = st.columns(3)

for col, mk in zip(exp_cols, ["safety","fuel","speed"]):
    if mk not in all_routes: continue
    meta   = MODE_META[mk]
    s      = all_stats.get(mk, {})
    smooth = douglas_peucker(all_routes[mk], 0.25)
    co2    = round(s.get("est_fuel_tons",0)*3.17,1)

    with col:
        st.markdown(f"**{meta['icon']} {meta['label']}**")

        df_wp = pd.DataFrame(smooth, columns=["latitude","longitude"])
        df_wp.insert(0,"waypoint", range(1,len(df_wp)+1))
        df_wp["lat_fmt"] = df_wp["latitude"].map( lambda x: f"{'N' if x>=0 else 'S'}{abs(x):.3f}°")
        df_wp["lon_fmt"] = df_wp["longitude"].map(lambda x: f"{'E' if x>=0 else 'W'}{abs(x):.3f}°")

        st.download_button(
            "⬇️ Waypoints CSV",
            data=df_wp.to_csv(index=False).encode(),
            file_name=f"route_{mk}_{start_p.split(',')[0]}_{end_p.split(',')[0]}.csv",
            mime="text/csv", use_container_width=True, key=f"csv_{mk}",
        )

        txt = (
            f"MARITIME DSS — VOYAGE REPORT\n"
            f"{'='*40}\n"
            f"Route:    {start_p} → {end_p}\n"
            f"Mode:     {meta['label']}\n"
            f"Ship:     {ship_type}  |  Fuel: {fuel_pct}%\n"
            f"{'='*40}\n"
            f"Distance: {s.get('distance_nm',0):.0f} NM\n"
            f"Duration: {s.get('est_hours',0):.0f} hrs ({s.get('est_days',0):.1f} days)\n"
            f"Speed:    {s.get('speed_knots',0)} kts\n"
            f"Fuel:     {s.get('est_fuel_tons',0):.1f} t\n"
            f"CO2:      {co2} kg\n"
            f"Avg wx:   {s.get('avg_weather_index',0):.2f}\n"
            f"Max wx:   {s.get('max_weather_index',0):.2f}\n"
            f"Waypoints:{len(smooth)} (smoothed)\n"
            f"{'Recommended ★' if mk==recommended else ''}\n"
            f"Generated:{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )
        st.download_button(
            "⬇️ Voyage Report TXT",
            data=txt.encode(),
            file_name=f"voyage_{mk}.txt",
            mime="text/plain", use_container_width=True, key=f"txt_{mk}",
        )

# ── EVENT LOG ─────────────────────────────────────────────────
if st.session_state.get("replan_log"):
    st.markdown('<div class="sec-hdr">Event log</div>', unsafe_allow_html=True)
    for ev in reversed(st.session_state.replan_log):
        dot = "#f59e0b" if ev["level"]=="warn" else "#34d399"
        st.markdown(f"""
<div style="display:flex;gap:10px;padding:6px 0;border-bottom:1px solid #112240;font-size:12px">
  <div style="width:8px;height:8px;border-radius:50%;background:{dot};margin-top:4px;flex-shrink:0"></div>
  <div><span style="color:#3a6080;font-size:10px">{ev['ts']}</span><br>
  <span style="color:#a8c0d8">{ev['msg']}</span></div>
</div>""", unsafe_allow_html=True)

# ── bottom nav ────────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
nb1, nb2, nb3 = st.columns([1, 3, 1])
with nb1:
    if st.button("← Back to Map", use_container_width=True):
        st.switch_page("pages/3_Route_Map.py")
with nb2:
    if st.button("🔄 Plan New Route", use_container_width=True):
        st.session_state.route_calculated = False
        st.session_state.all_routes       = {}
        st.session_state.all_stats        = {}
        st.session_state.replan_log       = []
        st.switch_page("pages/2_Constraints_Overview.py")
with nb3:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.switch_page("Login.py")
