"""
Login.py  —  Authentication Page (UPDATED)
============================================
✅ Password hashing (SHA-256)
✅ Register new user
✅ Session timeout (30 min)
✅ Role-based greeting
✅ Animated UI
✅ Correct page paths
"""

import streamlit as st
import hashlib
import time
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Maritime DSS — Login",
    page_icon="🚢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── helper: hash password ──
def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

# ── default demo users (hashed passwords) ──
DEFAULT_USERS = {
    "admin":   {"password": hash_password("maritime123"), "role": "Fleet Manager",  "avatar": "FM"},
    "captain": {"password": hash_password("ship2024"),    "role": "Ship Captain",   "avatar": "SC"},
    "analyst": {"password": hash_password("route456"),    "role": "Route Analyst",  "avatar": "RA"},
}

# ── load users from file (persistent new registrations) ──
USERS_FILE = "users_db.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_USERS.copy()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

USERS = load_users()

# ── session state init ──
for k, v in {
    "authenticated": False,
    "username": "",
    "login_time": 0,
    "nodes": None, "tree": None, "graph": None,
    "weather_loaded": False,
    "all_routes": {},
    "all_stats":  {},
    "replan_log": [],
    "current_mode": "safety",
    "selected_path": "safety",
    "route_calculated": False,
    "route_params": {},
    "show_register": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── session timeout check (30 min) ──
if st.session_state.authenticated:
    elapsed = time.time() - st.session_state.login_time
    if elapsed > 1800:
        st.session_state.authenticated = False
        st.warning("⏰ Session expired. Please login again.")
    else:
        st.switch_page("pages/2_Constraints_Overview.py")

# ── CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');

[data-testid="stAppViewContainer"] {
    background: #020c1a;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(0,60,120,0.15) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(0,100,80,0.1) 0%, transparent 50%);
}
[data-testid="stSidebar"]         { display: none; }
[data-testid="collapsedControl"]  { display: none; }
section[data-testid="stSidebarNav"]{ display: none; }

* { font-family: 'Exo 2', sans-serif !important; }

/* animated ocean grid background */
.ocean-bg {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background-image:
        linear-gradient(rgba(0,150,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,150,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    animation: grid-move 20s linear infinite;
    pointer-events: none; z-index: 0;
}
@keyframes grid-move {
    0%   { background-position: 0 0; }
    100% { background-position: 40px 40px; }
}

.login-wrap {
    max-width: 440px; margin: 30px auto 0;
    background: rgba(8, 20, 45, 0.95);
    border: 1px solid rgba(30,80,150,0.4);
    border-radius: 20px;
    padding: 40px 44px 36px;
    box-shadow: 0 0 60px rgba(0,100,200,0.1), 0 0 0 1px rgba(255,255,255,0.03);
    animation: fadein 0.6s ease;
}
@keyframes fadein {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

.ship-logo {
    text-align: center; margin-bottom: 8px;
    font-size: 52px;
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform: translateY(0px); }
    50%      { transform: translateY(-8px); }
}

.login-title {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 22px; font-weight: 700;
    color: #e2ecff; text-align: center;
    letter-spacing: 2px; margin-bottom: 4px;
}
.login-sub {
    font-size: 12px; color: #3a6080;
    text-align: center; margin-bottom: 28px;
    letter-spacing: 0.5px;
}

.demo-box {
    background: rgba(0,20,50,0.8);
    border: 1px solid rgba(30,80,150,0.3);
    border-left: 3px solid #1D9E75;
    border-radius: 8px; padding: 12px 14px;
    margin-bottom: 20px; font-size: 12px; color: #5a7fa8;
}
.demo-box b { color: #7ab8d8; }

input[type="text"], input[type="password"] {
    background: rgba(8, 25, 55, 0.9) !important;
    color: #e2ecff !important;
    border: 1px solid rgba(30,80,150,0.4) !important;
    border-radius: 8px !important;
}
input:focus {
    border-color: #1D9E75 !important;
    box-shadow: 0 0 0 2px rgba(29,158,117,0.15) !important;
}
label { color: #7a9cc0 !important; font-size: 12px !important; letter-spacing: 0.5px !important; }

.stButton > button {
    border-radius: 10px !important;
    font-family: 'Exo 2', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(29,158,117,0.3) !important; }

.divider {
    text-align: center; color: #1a3050;
    font-size: 12px; margin: 16px 0;
    position: relative;
}
.divider::before, .divider::after {
    content: ''; position: absolute; top: 50%;
    width: 42%; height: 1px; background: #112240;
}
.divider::before { left: 0; }
.divider::after  { right: 0; }

.footer-text {
    text-align: center; font-size: 11px;
    color: #1e3a5f; margin-top: 20px;
    letter-spacing: 0.5px;
}

/* role badges */
.role-badge {
    display: inline-block; font-size: 10px; font-weight: 600;
    padding: 3px 10px; border-radius: 20px; margin-top: 4px;
}
.role-FM { background: #083d20; color: #34d399; }
.role-SC { background: #082040; color: #60a5fa; }
.role-RA { background: #3b2600; color: #fbbf24; }
</style>
<div class="ocean-bg"></div>
""", unsafe_allow_html=True)

# ── UI ──
st.markdown("""
<div class="login-wrap">
  <div class="ship-logo">🚢</div>
  <div class="login-title">MARITIME DSS</div>
  <div class="login-sub">Dynamic Multi-Objective Ship Routing System</div>
</div>
""", unsafe_allow_html=True)

# ── tabs: Login / Register ──
tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Register"])

with tab_login:
    col_l, col_c, col_r = st.columns([1, 4, 1])
    with col_c:
        st.markdown("""
<div class="demo-box">
  <b>Demo Credentials</b><br>
  admin / maritime123 &nbsp;·&nbsp; captain / ship2024 &nbsp;·&nbsp; analyst / route456
</div>
""", unsafe_allow_html=True)

        username = st.text_input("USERNAME", placeholder="Enter username", key="login_user")
        password = st.text_input("PASSWORD", type="password", placeholder="Enter password", key="login_pass")

        if st.button("⚓  SIGN IN  →", type="primary", use_container_width=True):
            if username in USERS and USERS[username]["password"] == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.username      = username
                st.session_state.login_time    = time.time()
                st.session_state.user_role     = USERS[username]["role"]
                st.session_state.user_avatar   = USERS[username]["avatar"]

                role = USERS[username]["role"]
                greetings = {
                    "Fleet Manager":  "📊 Fleet systems online. All vessels accounted for.",
                    "Ship Captain":   "⚓ Captain on deck. Fair winds and following seas!",
                    "Route Analyst":  "🗺️ Routing systems ready. Charts are loaded.",
                }
                with st.spinner("🌊 Initializing Maritime Systems..."):
                    time.sleep(1.2)
                st.success(greetings.get(role, f"Welcome aboard, {username}!"))
                time.sleep(0.8)
                st.switch_page("pages/2_Constraints_Overview.py")
            else:
                st.error("❌ Invalid credentials. Check username & password.")

        st.markdown('<p class="footer-text">Indian Ocean Routing · Physics-based Weather · Dynamic A* Pathfinding</p>', unsafe_allow_html=True)

with tab_register:
    col_l, col_c, col_r = st.columns([1, 4, 1])
    with col_c:
        st.markdown("<p style='color:#5a7fa8;font-size:12px;margin-bottom:16px'>Create a new account to access Maritime DSS</p>", unsafe_allow_html=True)

        new_user = st.text_input("NEW USERNAME", placeholder="Choose a username", key="reg_user")
        new_pass = st.text_input("NEW PASSWORD", type="password", placeholder="Min 6 characters", key="reg_pass")
        confirm  = st.text_input("CONFIRM PASSWORD", type="password", placeholder="Re-enter password", key="reg_conf")
        new_role = st.selectbox("ROLE", ["Fleet Manager", "Ship Captain", "Route Analyst"], key="reg_role")

        if st.button("✅  CREATE ACCOUNT", type="primary", use_container_width=True):
            if not new_user or not new_pass:
                st.error("Username and password are required.")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pass != confirm:
                st.error("Passwords do not match.")
            elif new_user in USERS:
                st.error(f"Username '{new_user}' already exists.")
            else:
                USERS[new_user] = {
                    "password": hash_password(new_pass),
                    "role": new_role,
                    "avatar": "".join(w[0] for w in new_role.split())
                }
                save_users(USERS)
                st.success(f"✅ Account created! You can now login as **{new_user}**.")
                st.balloons()
