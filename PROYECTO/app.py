"""
app.py — ElectroDispatch AI v3 — UI Premium Rediseñada
"""
import io, time, json
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from agents import PriorityClassifier, ZoneCoverageAnalyzer, ejecutar_pipeline
from config import APP_VERSION, BOT_USERNAME, INVENTARIO_ALMACEN, TIPOS_INCIDENTE, ZONA_COLOR, ZONAS
from database import SQLiteManager

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="ElectroDispatch AI", page_icon="assets/logoELECTRO.png", layout="wide",
                   initial_sidebar_state="expanded")

@st.cache_resource
def get_db(): return SQLiteManager()
db = get_db()

# ── Design System CSS ─────────────────────────────────────────────────────────
st.markdown("""<style>
#particles-js { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; pointer-events: none; }
#cursor-glow { position: fixed; top: 0; left: 0; width: 600px; height: 600px; background: radial-gradient(circle, rgba(74, 143, 212, 0.15) 0%, transparent 70%); border-radius: 50%; pointer-events: none; z-index: 999999; transform: translate(-50%, -50%); mix-blend-mode: screen; display: block !important; }
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800;0,14..32,900&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ═══════════════════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════════════════ */
:root {
  --bg-base:    #050911;
  --bg-mid:     #080E1B;
  --glass:      rgba(255,255,255,0.035);
  --glass-hi:   rgba(255,255,255,0.065);
  --glass-bdr:  rgba(255,255,255,0.08);
  --glass-bdr-hi: rgba(233,184,74,0.3);
  --gold:       #E8B84B;
  --gold-lt:    #F5D080;
  --gold-dim:   rgba(232,184,75,0.10);
  --gold-glow:  rgba(232,184,75,0.20);
  --blue:       #4A8FD4;
  --blue-dim:   rgba(74,143,212,0.12);
  --emerald:    #10B981;
  --rose:       #F43F5E;
  --amber:      #F59E0B;
  --violet:     #8B5CF6;
  --text-hi:    #EBF4FF;
  --text-md:    #7097B5;
  --text-lo:    #374F65;
  --r-sm:       8px;
  --r-md:       14px;
  --r-lg:       20px;
  --r-xl:       28px;
  --shadow-sm:  0 2px 16px rgba(0,0,0,0.4);
  --shadow-md:  0 8px 32px rgba(0,0,0,0.5);
  --shadow-lg:  0 20px 60px rgba(0,0,0,0.6);
  --transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
}

/* ═══════════════════════════════════════════════════════
   BASE & RESET
═══════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* BACKGROUND — Subtle mesh gradient */
.stApp {
  background: var(--bg-base) !important;
  background-image:
    radial-gradient(ellipse 80% 60% at 70% -15%, rgba(74,143,212,0.09) 0%, transparent 65%),
    radial-gradient(ellipse 50% 40% at 5%  85%,  rgba(232,184,75,0.05) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 95% 50%,  rgba(139,92,246,0.04) 0%, transparent 70%) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(232,184,75,0.25); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(232,184,75,0.45); }

/* ═══════════════════════════════════════════════════════
   SIDEBAR — Professional dark panel
═══════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
  background: linear-gradient(175deg, #060D1C 0%, #040811 100%) !important;
  border-right: 1px solid rgba(255,255,255,0.055) !important;
  box-shadow: 2px 0 30px rgba(0,0,0,0.4) !important;
}
section[data-testid="stSidebar"] > div { padding: 0 !important; }

/* ═══════════════════════════════════════════════════════
   TABS — Pill navigation
═══════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: var(--glass) !important;
  border: 1px solid var(--glass-bdr) !important;
  border-radius: var(--r-lg) !important;
  padding: 5px !important;
  gap: 2px !important;
  backdrop-filter: blur(12px);
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-md) !important;
  font-weight: 600 !important;
  font-size: 0.81rem !important;
  border-radius: var(--r-md) !important;
  padding: 8px 18px !important;
  border: none !important;
  transition: var(--transition) !important;
  letter-spacing: 0.1px !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--text-hi) !important;
  background: var(--glass-hi) !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(232,184,75,0.15), rgba(232,184,75,0.08)) !important;
  color: var(--gold) !important;
  border: 1px solid var(--glass-bdr-hi) !important;
  box-shadow: 0 2px 12px rgba(232,184,75,0.15), inset 0 0 20px rgba(232,184,75,0.05) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 22px !important; }

/* ═══════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════ */
.stButton > button {
  background: linear-gradient(135deg, #E8B84B 0%, #C9920A 100%) !important;
  color: #060911 !important;
  font-weight: 700 !important;
  font-size: 0.84rem !important;
  border: none !important;
  border-radius: var(--r-sm) !important;
  padding: 9px 20px !important;
  letter-spacing: 0.2px !important;
  box-shadow: 0 2px 12px rgba(232,184,75,0.25) !important;
  transition: var(--transition) !important;
  position: relative !important;
  overflow: hidden !important;
}
.stButton > button::before {
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent) !important;
  opacity: 0 !important;
  transition: opacity 0.2s !important;
}
.stButton > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(232,184,75,0.35) !important;
}
.stButton > button:hover::before { opacity: 1 !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* Emergency */
.emer-wrap .stButton > button {
  background: linear-gradient(135deg, #6B1A1A 0%, #8B1A1A 100%) !important;
  color: #FFB3B3 !important;
  border: 1px solid rgba(244,63,94,0.35) !important;
  box-shadow: 0 3px 16px rgba(239,68,68,0.25) !important;
  font-size: 0.83rem !important;
}
.emer-wrap .stButton > button:hover {
  box-shadow: 0 6px 28px rgba(239,68,68,0.4) !important;
}

/* ═══════════════════════════════════════════════════════
   FORM ELEMENTS
═══════════════════════════════════════════════════════ */
div[data-baseweb="select"] > div,
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.09) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-hi) !important;
  font-size: 0.88rem !important;
  transition: var(--transition) !important;
}
div[data-baseweb="select"] > div:hover,
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
  border-color: var(--glass-bdr-hi) !important;
  background: rgba(255,255,255,0.06) !important;
  box-shadow: 0 0 0 3px rgba(232,184,75,0.12) !important;
  outline: none !important;
}
label[data-testid="stWidgetLabel"] p {
  color: var(--text-md) !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.7px !important;
  margin-bottom: 5px !important;
}

/* ═══════════════════════════════════════════════════════
   METRICS
═══════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
  background: var(--glass) !important;
  border: 1px solid var(--glass-bdr) !important;
  border-radius: var(--r-md) !important;
  padding: 16px 18px !important;
  transition: var(--transition) !important;
}
[data-testid="stMetric"]:hover {
  border-color: rgba(255,255,255,0.14) !important;
  background: var(--glass-hi) !important;
}
[data-testid="stMetricLabel"] > div {
  color: var(--text-md) !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.9px !important;
}
[data-testid="stMetricValue"] {
  color: var(--gold) !important;
  font-weight: 900 !important;
  font-size: 1.7rem !important;
  letter-spacing: -0.5px !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* ═══════════════════════════════════════════════════════
   EXPANDERS (cards in disguise)
═══════════════════════════════════════════════════════ */
details {
  background: var(--glass) !important;
  border: 1px solid var(--glass-bdr) !important;
  border-radius: var(--r-md) !important;
  transition: var(--transition) !important;
}
details:hover { border-color: rgba(255,255,255,0.13) !important; }
details[open] { border-color: rgba(232,184,75,0.18) !important; }
details summary {
  color: var(--text-hi) !important;
  font-weight: 600 !important;
  font-size: 0.86rem !important;
  padding: 12px 16px !important;
}
details summary:hover { color: var(--gold) !important; }

/* ═══════════════════════════════════════════════════════
   ALERTS
═══════════════════════════════════════════════════════ */
.stAlert {
  border-radius: var(--r-md) !important;
  border-left-width: 3px !important;
  font-size: 0.84rem !important;
}

/* ═══════════════════════════════════════════════════════
   DATAFRAME
═══════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--glass-bdr) !important;
  border-radius: var(--r-md) !important;
  overflow: hidden !important;
}

/* ═══════════════════════════════════════════════════════
   CUSTOM COMPONENTS
═══════════════════════════════════════════════════════ */

/* HERO BANNER */
.hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0B1A2E 0%, #0F2244 50%, #0E1C38 100%);
  border: 1px solid rgba(232,184,75,0.22);
  border-radius: var(--r-xl);
  padding: 28px 36px;
  margin-bottom: 24px;
}
.hero::before {
  content: '';
  position: absolute;
  top: -80px; right: -80px;
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(232,184,75,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.hero::after {
  content: '';
  position: absolute;
  bottom: -40px; left: -40px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(74,143,212,0.06) 0%, transparent 70%);
  pointer-events: none;
}
.hero h1 {
  color: var(--gold) !important;
  font-size: 2.1rem !important;
  font-weight: 900 !important;
  margin: 0 0 6px !important;
  letter-spacing: -1.2px !important;
  line-height: 1 !important;
  text-shadow: 0 0 40px rgba(232,184,75,0.35) !important;
}
.hero p {
  color: var(--text-md) !important;
  margin: 0 !important;
  font-size: 0.88rem !important;
  font-weight: 400 !important;
}
.badge {
  display: inline-block;
  background: linear-gradient(135deg, rgba(232,184,75,0.2), rgba(232,184,75,0.08));
  border: 1px solid var(--glass-bdr-hi);
  color: var(--gold);
  font-size: 0.62rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  margin-left: 10px;
  vertical-align: middle;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

/* KPI GRID */
.kgrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.kcard {
  position: relative;
  overflow: hidden;
  background: var(--glass);
  border: 1px solid var(--glass-bdr);
  border-radius: var(--r-md);
  padding: 16px 18px 14px;
  cursor: default;
  transition: var(--transition);
}
.kcard:hover {
  transform: translateY(-3px);
  border-color: rgba(255,255,255,0.14);
  box-shadow: var(--shadow-sm);
}
.kcard::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(to right, transparent, var(--kc, #E8B84B), transparent);
  opacity: 0.4;
}
.kcard::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: var(--kc, #E8B84B);
  opacity: 0.5;
  border-radius: 0 0 var(--r-md) var(--r-md);
}
.ki { font-size: 1.15rem; margin-bottom: 8px; opacity: 0.85; }
.kv {
  font-size: 2.1rem;
  font-weight: 900;
  color: var(--kc, #E8B84B);
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
  letter-spacing: -1px;
}
.kl {
  font-size: 0.65rem;
  color: var(--text-md);
  margin-top: 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

/* SECTION TITLE */
.stitle {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-hi);
  margin: 22px 0 12px;
  letter-spacing: -0.2px;
}
.stitle::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, rgba(255,255,255,0.08), transparent);
}

/* GLASS CARDS */
.card {
  background: var(--glass);
  border: 1px solid var(--glass-bdr);
  border-radius: var(--r-md);
  padding: 16px 18px;
  transition: var(--transition);
}
.card:hover { border-color: rgba(255,255,255,0.13); }

/* PRIORITY BADGES */
.pri { display:inline-flex; align-items:center; gap:4px; padding:3px 12px; border-radius:20px; font-size:0.7rem; font-weight:700; letter-spacing:0.4px; }
.p1 { background:rgba(244,63,94,0.12);  color:#F43F5E; border:1px solid rgba(244,63,94,0.28); }
.p2 { background:rgba(245,158,11,0.12); color:#F59E0B; border:1px solid rgba(245,158,11,0.28); }
.p3 { background:rgba(74,143,212,0.12); color:#4A8FD4; border:1px solid rgba(74,143,212,0.28); }
.p4 { background:rgba(16,185,129,0.12); color:#10B981; border:1px solid rgba(16,185,129,0.28); }

/* RISK BADGES */
.rb { display:inline-flex; align-items:center; padding:3px 12px; border-radius:20px; font-size:0.7rem; font-weight:700; }
.rb-BAJO    { background:rgba(16,185,129,0.1);  color:#10B981; border:1px solid rgba(16,185,129,0.22); }
.rb-MEDIO   { background:rgba(245,158,11,0.1);  color:#F59E0B; border:1px solid rgba(245,158,11,0.22); }
.rb-ALTO    { background:rgba(239,68,68,0.1);   color:#EF4444; border:1px solid rgba(239,68,68,0.22); }
.rb-CRITICO { background:rgba(244,63,94,0.12);  color:#F43F5E; border:1px solid rgba(244,63,94,0.28); }

/* AGENT TIMELINE */
.tl { padding-left: 20px; border-left: 2px solid rgba(232,184,75,0.2); margin: 10px 0; }
.tl-line { font-size: 0.82rem; color: var(--text-md); padding: 4px 0; line-height: 1.55; }
.tl-line::before { content: '›'; color: var(--gold); font-weight: 700; margin-right: 8px; opacity: 0.7; }

/* OT TERMINAL */
.ot-box {
  background: #020710;
  border: 1px solid rgba(232,184,75,0.15);
  border-radius: var(--r-md);
  padding: 24px 26px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.76rem;
  color: #7BAFC8;
  white-space: pre-wrap;
  line-height: 1.8;
  max-height: 500px;
  overflow-y: auto;
  box-shadow: inset 0 0 40px rgba(0,0,0,0.4), 0 0 0 1px rgba(232,184,75,0.05);
}

/* TELEGRAM MESSAGES */
.tgc {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  padding: 14px 16px;
  background: var(--glass);
  border: 1px solid var(--glass-bdr);
  border-radius: var(--r-md);
  transition: var(--transition);
}
.tgc.nuevo { border-color: rgba(232,184,75,0.28); background: rgba(232,184,75,0.06); }
.tgc:hover { border-color: rgba(255,255,255,0.12); transform: translateX(2px); }
.av {
  width: 38px; height: 38px; flex-shrink: 0;
  background: linear-gradient(135deg, #1B3B5E, #2C5C90);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.88rem; font-weight: 700; color: var(--gold);
  border: 1px solid rgba(74,143,212,0.25);
}
.tg-name { font-weight: 700; font-size: 0.84rem; color: var(--text-hi); }
.tg-time { font-size: 0.7rem; color: var(--text-lo); margin-left: 8px; }
.tg-cnt  { font-size: 0.83rem; color: var(--text-md); margin-top: 4px; line-height: 1.4; }
.tipo-foto { background: rgba(74,143,212,0.12); color: #4A8FD4; border-radius: 8px; padding: 2px 8px; font-size: 0.67rem; font-weight: 700; }
.tipo-txt  { background: rgba(16,185,129,0.12); color: #10B981; border-radius: 8px; padding: 2px 8px; font-size: 0.67rem; font-weight: 700; }

/* STATUS DOTS */
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; vertical-align:middle; }
.dot-ok   { background:#10B981; box-shadow:0 0 8px rgba(16,185,129,0.6); }
.dot-warn { background:#F59E0B; box-shadow:0 0 8px rgba(245,158,11,0.6); }
.dot-err  { background:#F43F5E; box-shadow:0 0 8px rgba(244,63,94,0.6); }

/* ANIMATIONS */
@keyframes pulse { 0%,100%{opacity:1; transform:scale(1)} 50%{opacity:0.5; transform:scale(1.2)} }
.pulse { animation: pulse 1.8s ease-in-out infinite; }

@keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
.fade-up { animation: fadeUp 0.4s ease forwards; }

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.shimmer-line {
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.07) 50%, rgba(255,255,255,0.03) 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 6px; height: 12px;
}

/* SIDEBAR LABEL */
.sb-label {
  font-size: 0.6rem;
  font-weight: 700;
  color: var(--text-lo);
  text-transform: uppercase;
  letter-spacing: 2px;
  padding: 10px 14px 4px;
}
</style>
<div id="particles-js"></div>
<div id="cursor-glow"></div>
<script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
<script>
function initFX() {
  if (typeof particlesJS !== 'undefined') {
    particlesJS("particles-js", {
      "particles": {
        "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
        "color": { "value": "#4a8fd4" },
        "shape": { "type": "circle" },
        "opacity": { "value": 0.4, "random": false },
        "size": { "value": 2, "random": true },
        "line_linked": { "enable": true, "distance": 150, "color": "#4a8fd4", "opacity": 0.25, "width": 1 },
        "move": { "enable": true, "speed": 1.8, "direction": "none", "random": false, "straight": false, "out_mode": "out", "bounce": false }
      },
      "interactivity": { "detect_on": "canvas", "events": { "onhover": { "enable": false }, "onclick": { "enable": false }, "resize": true } },
      "retina_detect": true
    });
    const glow = document.getElementById('cursor-glow');
    const update = (e) => {
      glow.style.left = e.clientX + 'px';
      glow.style.top = e.clientY + 'px';
    };
    window.addEventListener('mousemove', update);
    if (window.parent) window.parent.addEventListener('mousemove', update);
  } else {
    setTimeout(initFX, 200);
  }
}
initFX();
</script>""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def kcard(val, lbl, ico, color="#E9B84A"):
    return f'<div class="kcard" style="--kc:{color}"><div class="ki">{ico}</div><div class="kv" style="color:{color}">{val}</div><div class="kl">{lbl}</div></div>'

def rbadge(nivel):
    return f'<span class="rb rb-{nivel}">{nivel}</span>'

def pbadge(num, nivel):
    cls = f"p{num}"
    return f'<span class="pri {cls}">P{num} {nivel}</span>'

def stitle(t):
    st.markdown(f'<div class="stitle">{t}</div>', unsafe_allow_html=True)

def hdiv():
    st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,.06);margin:14px 0">', unsafe_allow_html=True)

def dlayout():
    return {"paper_bgcolor":"rgba(0,0,0,0)","plot_bgcolor":"rgba(0,0,0,0)",
            "font":{"color":"#7A9BBC","family":"Inter"},"title":{"font":{"color":"#E9B84A","size":13}},
            "xaxis":{"gridcolor":"rgba(255,255,255,.06)","color":"#5A7A9A"},
            "yaxis":{"gridcolor":"rgba(255,255,255,.06)","color":"#5A7A9A"},
            "margin":{"l":10,"r":10,"t":36,"b":10},"legend":{"font":{"color":"#7A9BBC"}}}

# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown("""<div style="padding:18px 16px 14px;border-bottom:1px solid rgba(255,255,255,.06)">
        <div style="font-size:1rem;font-weight:900;color:#E9B84A;letter-spacing:-.5px">⚡ ElectroDispatch</div>
        <div style="font-size:.65rem;color:#3D5F7C;margin-top:2px;text-transform:uppercase;letter-spacing:1.5px">Dispatch AI · v3.0</div>
        </div>""", unsafe_allow_html=True)

        # ─ Logo header ─────────────────────────────────────
        st.markdown(f"""<div style="padding:22px 18px 16px;border-bottom:1px solid rgba(255,255,255,0.06);position:relative;overflow:hidden">
  <div style="position:absolute;top:-30px;right:-30px;width:120px;height:120px;
              background:radial-gradient(circle,rgba(232,184,75,0.08) 0%,transparent 70%);pointer-events:none"></div>
  <div style="display:flex;align-items:center;gap:10px">
    <div style="width:34px;height:34px;background:linear-gradient(135deg,#2A1F00,#4A3500);
                border:1px solid rgba(232,184,75,0.4);border-radius:10px;
                display:flex;align-items:center;justify-content:center;font-size:1.1rem">⚡</div>
    <div>
      <div style="font-size:0.95rem;font-weight:800;color:#E8B84B;letter-spacing:-0.5px;line-height:1">ElectroDispatch</div>
      <div style="font-size:0.6rem;color:#374F65;margin-top:2px;text-transform:uppercase;letter-spacing:2px">AI · Sistema {APP_VERSION}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # ─ Flota status ─────────────────────────────────────
        flota = db.get_flota()
        disp = sum(1 for v in flota if v["estado"]=="Disponible")
        ocup = sum(1 for v in flota if v["estado"]=="Ocupado")
        mant = sum(1 for v in flota if v["estado"]=="Mantenimiento")
        total = len(flota) or 1
        pct  = int(disp/total*100)
        pct_o = int(ocup/total*100)
        pct_m = int(mant/total*100)

        st.markdown(f"""<div style="padding:14px 18px 12px">
  <div class="sb-label">Estado de Flota</div>
  <div style="display:flex;gap:6px;margin:8px 0 6px">
    <div style="flex:{disp or 0.001};height:5px;background:#10B981;border-radius:3px 0 0 3px;
                box-shadow:0 0 8px rgba(16,185,129,0.4);transition:flex .5s"></div>
    <div style="flex:{ocup or 0.001};height:5px;background:#F43F5E;
                box-shadow:0 0 8px rgba(244,63,94,0.4);transition:flex .5s"></div>
    <div style="flex:{mant or 0.001};height:5px;background:#F59E0B;border-radius:0 3px 3px 0;
                box-shadow:0 0 8px rgba(245,158,11,0.4);transition:flex .5s"></div>
  </div>
  <div style="display:flex;justify-content:space-between;margin-top:6px">
    <span style="font-size:0.72rem;color:#10B981;font-weight:600">🟢 {disp} disp.</span>
    <span style="font-size:0.72rem;color:#F43F5E;font-weight:600">🔴 {ocup} ocup.</span>
    <span style="font-size:0.72rem;color:#F59E0B;font-weight:600">🔧 {mant} mant.</span>
  </div>
  <div style="font-size:0.65rem;color:#374F65;margin-top:4px">{pct}% disponibilidad · {total} vehículos</div>
</div>""", unsafe_allow_html=True)

        for v in flota:
            ec = {"Disponible":"#10B981","Ocupado":"#F43F5E","Mantenimiento":"#F59E0B"}.get(v["estado"],"#888")
            ti = {"Grúa":"🏗️","Canasta":"🪣","Ligero":"🚐"}.get(v["tipo"],"🚗")
            with st.expander(f"{ti} {v['id']}", expanded=False):
                st.markdown(f"""<div style="font-size:0.78rem;padding:2px 0">
  <span style="color:{ec};font-weight:700">{v['estado']}</span>
  <span style="color:#374F65"> · {v['tipo']} · {v['capacidad_ton']}t</span><br>
  <span style="color:#7097B5">👤 {v['chofer']}</span><br>
  <span style="color:#374F65">📍 {v['zona']}</span>
</div>""", unsafe_allow_html=True)

        # ─ Alertas ─────────────────────────────────────────
        hdiv()
        alertas = db.get_alertas_activas()
        if alertas:
            st.markdown(f'<div class="sb-label" style="color:#F43F5E">🚨 Alertas activas ({len(alertas)})</div>', unsafe_allow_html=True)
            for a in alertas[:2]:
                st.error(a["mensaje"][:65])

        # ─ Telegram live ───────────────────────────────────
        hdiv()
        rep = db.get_estadisticas()
        nuevos = rep.get("nuevos_telegram", 0)
        dot_cl = "dot-err pulse" if nuevos > 0 else "dot-ok"
        st.markdown(f"""<div style="padding:4px 18px 10px">
  <div class="sb-label">Bot Telegram</div>
  <div style="display:flex;align-items:center;gap:8px;margin-top:6px;padding:8px 12px;
              background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
              border-radius:10px">
    <span class="dot {dot_cl}"></span>
    <span style="font-size:0.8rem;color:#7097B5;font-weight:600">{BOT_USERNAME}</span>
    {"<span style='margin-left:auto;background:rgba(244,63,94,0.15);color:#F43F5E;font-size:0.67rem;font-weight:700;padding:2px 8px;border-radius:20px;border:1px solid rgba(244,63,94,0.3)'>" + str(nuevos) + " nuevo" + ("s" if nuevos!=1 else "") + "</span>" if nuevos > 0 else "<span style='margin-left:auto;font-size:0.67rem;color:#374F65'>En línea</span>"}
  </div>
</div>""", unsafe_allow_html=True)

        # ─ Items bajo stock ─────────────────────────────────
        items_bajos = db.get_items_bajo_stock()
        if items_bajos:
            st.markdown(f'<div class="sb-label" style="color:#F59E0B">📦 Stock bajo ({len(items_bajos)})</div>', unsafe_allow_html=True)
            for it in items_bajos[:3]:
                st.markdown(f'<div style="padding:2px 18px;font-size:0.73rem;color:#F59E0B">⚠️ {it["item"][:28]} — {it["cantidad"]} {it["unidad"]}</div>', unsafe_allow_html=True)

        # ─ Emergencia ──────────────────────────────────────
        hdiv()
        st.markdown('<div class="sb-label">Acción Rápida</div>', unsafe_allow_html=True)
        st.markdown('<div style="padding:4px 12px 10px">', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="emer-wrap">', unsafe_allow_html=True)
            if st.button("🚨 DESPACHO URGENTE", use_container_width=True, key="emer_btn"):
                st.session_state["modo_emergencia"] = True
                st.session_state["active_tab"] = 1
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ── Tab 1: Dashboard ──────────────────────────────────────────────────────────
def tab_dashboard():
    stats = db.get_estadisticas()
    kh = '<div class="kgrid">'
    kh += kcard(stats["disponibles"],   "Disponibles",     "🟢", "#10B981")
    kh += kcard(stats["ot_hoy"],        "OTs Hoy",         "📋", "#E9B84A")
    kh += kcard(stats["alertas_activas"],"Alertas",        "🚨", "#F43F5E")
    kh += kcard(stats["total_ot"],      "OTs Históricas",  "📊", "#4E90D3")
    kh += kcard(stats["nuevos_telegram"],"Nuevos Bot",     "📱", "#8B5CF6")
    kh += kcard(stats["total_flota"],   "Flota Total",     "🚛", "#E9B84A")
    kh += kcard(stats.get("stock_bajo",0), "Stock Bajo",  "📦", "#F43F5E" if stats.get("stock_bajo",0) else "#10B981")
    kh += '</div>'
    st.markdown(kh, unsafe_allow_html=True)

    col_mapa, col_act = st.columns([1, 2], gap="large")

    with col_mapa:
        stitle("Mapa de Zonas")
        flota = db.get_flota()
        disp_z = {}
        tot_z  = {}
        for v in flota:
            z = v["zona"]
            tot_z[z]  = tot_z.get(z,0) + 1
            disp_z[z] = disp_z.get(z,0) + (1 if v["estado"]=="Disponible" else 0)

        from config import ZONA_GRID, ZONA_COLOR
        
        # Agrupar zonas por fila del grid
        max_f = max(pos[0] for pos in ZONA_GRID.values())
        max_c = max(pos[1] for pos in ZONA_GRID.values())
        
        # Crear matriz para renderizado
        grid_matrix = [[None for _ in range(max_c + 1)] for _ in range(max_f + 1)]
        for z, pos in ZONA_GRID.items():
            grid_matrix[pos[0]][pos[1]] = z

        rows = []
        for fila in grid_matrix:
            cells = []
            for z in fila:
                if z is None:
                    cells.append('<td style="border:none"></td>')
                    continue
                c = ZONA_COLOR.get(z,"#444")
                d = disp_z.get(z,0); t = tot_z.get(z,0)
                pct_z = int(d/t*100) if t else 0
                cells.append(f'<td style="background:{c}18;border:1px solid {c}40;border-radius:10px;padding:10px 6px;text-align:center;min-width:86px"><div style="color:{c};font-weight:800;font-size:.72rem">{z}</div><div style="color:rgba(255,255,255,.5);font-size:.65rem;margin-top:2px">🟢{d}/{t} · {pct_z}%</div></td>')
            rows.append("<tr>" + "".join(cells) + "</tr>")
        
        st.markdown(f'<table style="border-collapse:separate;border-spacing:6px;width:100%">{"".join(rows)}</table>', unsafe_allow_html=True)

        # Análisis de cobertura
        hdiv()
        stitle("Análisis de Cobertura")
        analisis = ZoneCoverageAnalyzer().analizar(db)
        if analisis["recomendaciones"]:
            for rec in analisis["recomendaciones"][:3]:
                st.warning(rec)
        else:
            st.success("✅ Cobertura adecuada en todas las zonas.")

    with col_act:
        c1, c2 = st.columns([3,1])
        with c1: stitle("Actividad Reciente")
        with c2:
            if st.button("🗑️ Vaciar", help="Borrar todo el historial de actividad"):
                db.vaciar_actividades(); st.rerun()
                
        ots = db.get_incidentes(limit=10)
        if not ots:
            st.info("Sin órdenes de trabajo. Crea una en el tab ⚡ Despacho.")
        for ot in ots:
            nivel = ot.get("nivel_riesgo","N/D")
            ts = ot.get("created_at","")[:16].replace("T"," ")
            src = "📱" if ot.get("fuente")=="telegram" else "🖥️"
            
            c_info, c_del = st.columns([9,1])
            with c_info:
                st.markdown(f"""<div class="card" style="margin-bottom:8px;border-left:3px solid rgba(233,184,74,.4)">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <span style="color:#E9B84A;font-weight:700;font-size:.85rem">{src} {ot.get('numero_ot','?')}</span>
                  {rbadge(nivel)} <span style="color:#3D5F7C;font-size:.72rem">{ts}</span>
                </div>
                <div style="color:#7A9BBC;font-size:.78rem;margin-top:5px">📍 {ot.get('zona','?')} · 🚛 {ot.get('vehiculo_asignado','?')} · ⏱️ {ot.get('eta_min','?')} min</div>
                <div style="color:#3D5F7C;font-size:.74rem;margin-top:2px">{str(ot.get('descripcion',''))[:90]}…</div>
                </div>""", unsafe_allow_html=True)
            with c_del:
                if st.button("🗑️", key=f"del_ot_{ot['id']}", help="Eliminar esta actividad"):
                    db.eliminar_incidente(ot["id"]); st.rerun()

    # Alertas activas
    alertas = db.get_alertas_activas()
    if alertas:
        hdiv(); stitle("🚨 Alertas de Seguridad Activas")
        for a in alertas:
            c1, c2 = st.columns([9,1])
            with c1:
                st.markdown(f"""<div class="card">
                {rbadge(a.get('nivel','MEDIO'))} <span style="color:#E9B84A;font-weight:700;margin-left:8px">{a.get('tipo','')}</span>
                <span style="color:#3D5F7C;font-size:.72rem;margin-left:8px">{a.get('created_at','')[:16].replace('T',' ')}</span>
                <div style="color:#7A9BBC;font-size:.8rem;margin-top:4px">📍 {a.get('zona','?')} — {a.get('mensaje','')}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                if st.button("✕", key=f"ca_{a['id']}"):
                    db.cerrar_alerta(a["id"]); st.rerun()

# ── Tab 2: Despacho ───────────────────────────────────────────────────────────
def tab_despacho():
    es_emer = st.session_state.pop("modo_emergencia", False)

    stitle("⚡ Registrar Incidente")

    # Pre-fill emergencia
    desc_default = "⚠️ EMERGENCIA — " if es_emer else (st.session_state.pop("despacho_prefill",""))
    if es_emer:
        st.error("🚨 MODO EMERGENCIA ACTIVADO — Prioridad máxima. Completa los datos y despacha.")

    col_f, col_i = st.columns([2,1], gap="large")
    with col_f:
        with st.form("dispatch_form"):
            tipo = st.selectbox("🔷 Tipo de incidente", TIPOS_INCIDENTE)
            desc = st.text_area("📌 Descripción", value=desc_default, height=100,
                                placeholder="Ubicación exacta, cables caídos, personas en riesgo...")
            c1,c2 = st.columns(2)
            zona  = c1.selectbox("📍 Zona", ZONAS, index=0 if not es_emer else ZONAS.index("Centro"))
            clima = c2.selectbox("🌤️ Clima", ["Soleado","Nublado","Lluvioso","Tormenta"],
                                 index=3 if es_emer else 0)
            submitted = st.form_submit_button("⚡ Iniciar Despacho Inteligente", use_container_width=True)

    with col_i:
        stitle(f"Estado · {datetime.now().strftime('%H:%M')}")
        stats = db.get_estadisticas()
        st.metric("🟢 Disponibles", stats["disponibles"])
        st.metric("📋 OTs Hoy",     stats["ot_hoy"])

        if desc and not submitted:
            hdiv()
            stitle("Vista Previa Prioridad")
            pc = PriorityClassifier()
            prev = pc.run(desc or tipo, tipo)
            pdat = prev.datos
            st.markdown(f'<div class="card" style="text-align:center;padding:18px">{pbadge(pdat["numero"],pdat["nivel"])}<div style="color:#7A9BBC;font-size:.78rem;margin-top:8px">ETA máximo: {pdat["tiempo_max_min"]} min</div></div>', unsafe_allow_html=True)

    if submitted:
        desc_f = desc.strip() or tipo
        hdiv(); stitle("🤖 Pipeline en Ejecución")

        with st.status("⚙️ Ejecutando agentes...", expanded=True) as status:
            st.write("🔵 P0 — Clasificando prioridad...")
            time.sleep(0.4)
            st.write("🔵 P1 — Buscando vehículo óptimo...")
            time.sleep(0.6)
            st.write("🔵 P2 — Evaluando condiciones de seguridad...")
            time.sleep(0.5)
            resultado = ejecutar_pipeline(desc_f, tipo, zona, clima, db, "web")
            time.sleep(0.4)
            st.write("🔵 P3 — Generando Orden de Trabajo...")
            time.sleep(0.4)
            status.update(label="✅ Pipeline completado" if resultado["exito"] else "❌ Fallo", state="complete" if resultado["exito"] else "error")

        if not resultado["exito"]:
            r1 = resultado.get("agente1")
            st.error(r1.error if r1 else "Error desconocido")
            return

        r0d = resultado["agente0"].datos
        r1d = resultado["agente1"].datos
        r2d = resultado["agente2"].datos
        r3d = resultado["agente3"].datos

        # Agente logs
        tabs_a = st.tabs(["P0 · Prioridad","P1 · Logística","P2 · Seguridad","P3 · AdminBot"])
        for tab_a, key in zip(tabs_a, ["agente0","agente1","agente2","agente3"]):
            with tab_a:
                r = resultado.get(key)
                if r:
                    st.markdown('<div class="tl">' + ''.join(f'<div class="tl-line">{lg}</div>' for lg in r.logs) + '</div>', unsafe_allow_html=True)

        hdiv(); stitle("🏆 Resultado")
        cols = st.columns(5)
        cols[0].metric("🔴 Prioridad",  f"{r0d['emoji']} {r0d['nivel']}")
        cols[1].metric("🚛 Vehículo",   r1d["id_vehiculo"])
        cols[2].metric("👤 Chofer",     r1d["chofer"])
        cols[3].metric("⏱️ ETA",        f"{r1d['tiempo_estimado_min']} min")
        cols[4].metric("🛡️ Riesgo",     r2d["nivel_riesgo"])

        if not r1d.get("eta_ok", True):
            st.warning(f"⚠️ ETA supera el tiempo máximo para prioridad {r0d['nivel']} ({r0d['tiempo_max_min']} min). Considere alertar al supervisor.")

        if r2d.get("advertencias"):
            for adv in r2d["advertencias"]:
                st.warning(adv)

        if r2d.get("epp_requerido"):
            with st.expander(f"🦺 EPP Requerido — {len(r2d['epp_requerido'])} ítems"):
                cols_e = st.columns(3)
                for i, itm in enumerate(r2d["epp_requerido"]):
                    cols_e[i%3].markdown(f"✓ {itm}")

        hdiv(); stitle("📄 Orden de Trabajo")
        st.markdown(f'<div class="ot-box">{r3d["texto_ot"]}</div>', unsafe_allow_html=True)

        hdiv()
        bot = resultado.get("admin_bot")
        if bot:
            pdf = bot.generar_pdf(r3d["texto_ot"], r3d["numero_ot"], r0d.get("numero",3))
            if pdf:
                st.download_button("📥 Descargar OT en PDF", data=pdf,
                    file_name=f"{r3d['numero_ot']}.pdf", mime="application/pdf")

# ── Tab 3: Telegram ───────────────────────────────────────────────────────────
def tab_telegram():
    stitle(f"📱 Central {BOT_USERNAME}")
    c1,c2,c3 = st.columns([3,1,1])
    auto = c1.checkbox("🔄 Auto-refresh cada 10s")
    if c2.button("↻ Actualizar"): st.rerun()
    stats = db.get_estadisticas()
    c3.metric("Nuevos", stats["nuevos_telegram"])

    with st.expander("ℹ️ Configuración del Bot"):
        st.markdown(f"""
**Bot:** {BOT_USERNAME}  
1. Abre Telegram → busca {BOT_USERNAME}  
2. `/start` para activar  
3. Envía **fotos** del incidente → aparecen aquí  
4. `/ot descripcion | zona` para crear OTs desde el móvil  
5. Terminal separada: `python telegram_bot.py`
        """)
    hdiv()

    reportes = db.get_reportes_telegram(limit=25)
    if not reportes:
        st.info(f"📭 Sin reportes aún. Envía fotos a {BOT_USERNAME}"); return

    for rep in reportes:
        nuevo = not rep.get("procesado",0)
        tipo  = rep.get("tipo","texto")
        cls   = "tgc nuevo" if nuevo else "tgc"
        ts    = rep.get("created_at","")[:16].replace("T"," ")
        initials = (rep.get("nombre","?")[:2]).upper()
        badge_t = f'<span class="tipo-foto">FOTO</span>' if tipo=="foto" else f'<span class="tipo-txt">TEXTO</span>'

        cr, ca = st.columns([6,1])
        with cr:
            st.markdown(f"""<div class="{cls}">
            <div class="av">{initials}</div>
            <div style="flex:1">
              <div><span class="tg-name">{rep.get('nombre','?')}</span><span class="tg-time">@{rep.get('username','?')} · {ts}</span> {badge_t}{'<span style="color:#E9B84A;font-size:.7rem;margin-left:6px">● NUEVO</span>' if nuevo else ''}</div>
              <div class="tg-cnt">{rep.get('contenido','')}</div>
            </div></div>""", unsafe_allow_html=True)
            if tipo == "foto":
                _show_photo(rep["id"])
        with ca:
            if nuevo:
                if st.button("✅", key=f"p_{rep['id']}", help="Marcar como procesado"):
                    db.marcar_procesado(rep['id']); st.rerun()
            
            if st.button("🚀", key=f"d_{rep['id']}", help="Copiar al Despacho"):
                st.session_state["despacho_prefill"] = rep.get("contenido","")
                st.toast("✅ Datos copiados al Despacho")
            
            if st.button("🗑️", key=f"del_tg_{rep['id']}", help="Eliminar reporte permanentemente"):
                db.eliminar_reporte_telegram(rep['id'])
                st.toast("🗑️ Reporte eliminado")
                st.rerun()

        # Respuesta rápida (Solo si no es foto o si tiene chat_id)
        if rep.get("chat_id"):
            with st.expander(f"✉️ Responder a {rep.get('nombre','usuario')}", expanded=False):
                with st.form(f"resp_{rep['id']}"):
                    msj_resp = st.text_area("Mensaje", placeholder="Escribe tu respuesta aquí...", key=f"txt_resp_{rep['id']}", label_visibility="collapsed")
                    if st.form_submit_button("Enviar Mensaje 📤"):
                        from config import TELEGRAM_TOKEN
                        if not TELEGRAM_TOKEN:
                            st.error("Error: Token de Telegram no configurado en config.py")
                        else:
                            try:
                                import asyncio
                                from telegram import Bot
                                bot_tg = Bot(TELEGRAM_TOKEN)
                                
                                async def env():
                                    await bot_tg.send_message(chat_id=rep['chat_id'], text=f"📥 *Respuesta Central:* {msj_resp}", parse_mode="Markdown")
                                
                                # Ejecutar en hilo separado para no bloquear Streamlit
                                import threading
                                def run_async_env():
                                    asyncio.run(env())
                                
                                threading.Thread(target=run_async_env).start()
                                st.success("Mensaje enviado con éxito!")
                            except Exception as e:
                                st.error(f"Error al enviar: {e}")

    if auto: time.sleep(10); st.rerun()

def _show_photo(rid):
    import sqlite3
    try:
        con = sqlite3.connect("electrodispatch.db", check_same_thread=False)
        r = con.execute("SELECT foto_bytes FROM reportes_telegram WHERE id=?", (rid,)).fetchone()
        con.close()
        if r and r[0]:
            st.image(io.BytesIO(r[0]), use_container_width=True, caption="📸 Foto del incidente")
    except: pass

# ── Tab 4: Estadísticas ───────────────────────────────────────────────────────
def tab_estadisticas():
    stitle("📊 Estadísticas del Sistema")
    ots = db.get_incidentes(limit=200)
    if not ots:
        st.info("Genera OTs en el tab Despacho para ver estadísticas.")
        _demo_charts(); return

    df = pd.DataFrame(ots)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total OTs", len(df))
    if "zona" in df.columns and not df["zona"].empty:
        c2.metric("Zona top", df["zona"].value_counts().index[0])
    if "nivel_riesgo" in df.columns and not df["nivel_riesgo"].empty:
        c3.metric("Riesgo frecuente", df["nivel_riesgo"].value_counts().index[0])
    if "eta_min" in df.columns:
        c4.metric("ETA prom.", f"{int(df['eta_min'].mean())} min")

    hdiv()
    col1, col2 = st.columns(2, gap="large")
    with col1:
        if "zona" in df.columns:
            vc = df["zona"].value_counts().reset_index(); vc.columns=["Zona","OTs"]
            fig = px.bar(vc,x="Zona",y="OTs",title="OTs por Zona",color="OTs",
                         color_continuous_scale=["#1A3A5C","#E9B84A"])
            fig.update_layout(**dlayout()); st.plotly_chart(fig, use_container_width=True)
    with col2:
        if "nivel_riesgo" in df.columns:
            vc = df["nivel_riesgo"].value_counts().reset_index(); vc.columns=["Riesgo","Total"]
            cm = {"BAJO":"#10B981","MEDIO":"#F59E0B","ALTO":"#EF4444","CRITICO":"#F43F5E"}
            fig = px.pie(vc,names="Riesgo",values="Total",title="Distribución por Riesgo",
                         color="Riesgo",color_discrete_map=cm,hole=.45)
            fig.update_layout(**dlayout()); st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2, gap="large")
    with col3:
        if "vehiculo_asignado" in df.columns and "eta_min" in df.columns:
            ve = df.groupby("vehiculo_asignado")["eta_min"].mean().reset_index()
            ve.columns=["Vehículo","ETA prom (min)"]
            fig = px.bar(ve,x="Vehículo",y="ETA prom (min)",title="ETA por Vehículo",
                         color_discrete_sequence=["#4E90D3"])
            fig.update_layout(**dlayout()); st.plotly_chart(fig, use_container_width=True)
    with col4:
        if "created_at" in df.columns:
            df["fecha"] = pd.to_datetime(df["created_at"]).dt.date
            tl = df.groupby("fecha").size().reset_index(name="OTs")
            fig = px.line(tl,x="fecha",y="OTs",title="OTs por Día",line_shape="spline",
                          color_discrete_sequence=["#E9B84A"])
            fig.update_traces(fill="tozeroy",fillcolor="rgba(233,184,74,.07)")
            fig.update_layout(**dlayout()); st.plotly_chart(fig, use_container_width=True)

    hdiv(); stitle("📋 Historial")
    cols_v = [c for c in ["numero_ot","tipo_incidente","zona","vehiculo_asignado","eta_min","nivel_riesgo","created_at","fuente"] if c in df.columns]
    st.dataframe(df[cols_v], use_container_width=True, hide_index=True)

    if st.button("📥 Exportar CSV"):
        st.download_button("⬇️ Descargar CSV", df[cols_v].to_csv(index=False).encode(),
                           "electrodispatch_historial.csv", "text/csv")

def _demo_charts():
    import numpy as np
    zonas_d = ["Norte","Sur","Este","Oeste","Centro","Industrial"]
    vals_d = [12,8,15,6,20,4]
    fig = px.bar(x=zonas_d,y=vals_d,title="(Demo) Actividad por Zona",
                 color=vals_d,color_continuous_scale=["#1A3A5C","#E9B84A"])
    fig.update_layout(**dlayout()); st.plotly_chart(fig, use_container_width=True)

# ── Tab 5: Flota con CRUD completo ───────────────────────────────────────────
def tab_flota():
    stitle("🚛 Gestión de Flota en Tiempo Real")
    flota = db.get_flota()
    disp=sum(1 for v in flota if v["estado"]=="Disponible")
    ocup=sum(1 for v in flota if v["estado"]=="Ocupado")
    mant=sum(1 for v in flota if v["estado"]=="Mantenimiento")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Total",len(flota)); c2.metric("🟢 Disponibles",disp); c3.metric("🔴 Ocupados",ocup); c4.metric("🔧 Mantenimiento",mant)

    # ── Agregar vehículo ──────────────────────────────────────────────────────
    with st.expander("➕ Agregar Nuevo Vehículo", expanded=False):
        with st.form("add_v"):
            ca,cb,cc = st.columns(3)
            nid   = ca.text_input("ID Vehículo*", placeholder="VH-016")
            ntipo = cb.selectbox("Tipo*", ["Grúa","Canasta","Ligero"])
            nzona = cc.selectbox("Zona*", ZONAS)
            cd,ce,cf = st.columns(3)
            nch   = cd.text_input("Chofer*", placeholder="Juan Pérez")
            ncap  = ce.number_input("Capacidad (t)", 0.5, 30.0, 1.0, 0.5)
            nest  = cf.selectbox("Estado inicial", ["Disponible","Ocupado","Mantenimiento"])
            ok = st.form_submit_button("✅ Agregar", use_container_width=True)
        if ok:
            if not nid or not nch:
                st.error("ID y Chofer son obligatorios.")
            else:
                exito = db.agregar_vehiculo({"id":nid.strip().upper(),"tipo":ntipo,"estado":nest,
                                             "zona":nzona,"chofer":nch.strip(),"capacidad_ton":ncap})
                if exito:
                    st.success(f"✅ Vehículo {nid} agregado."); st.rerun()
                else:
                    st.error(f"❌ El ID '{nid}' ya existe.")

    hdiv()
    col_f1,col_f2,col_f3=st.columns(3)
    fil_est=col_f1.multiselect("Estado",["Disponible","Ocupado","Mantenimiento"],default=["Disponible","Ocupado","Mantenimiento"])
    fil_tip=col_f2.multiselect("Tipo",["Grúa","Canasta","Ligero"],default=["Grúa","Canasta","Ligero"])
    fil_zon=col_f3.multiselect("Zona",ZONAS,default=ZONAS)
    filt=[v for v in flota if v["estado"] in fil_est and v["tipo"] in fil_tip and v["zona"] in fil_zon]
    stitle(f"Vehículos ({len(filt)} de {len(flota)})")

    for i in range(0,len(filt),3):
        batch=filt[i:i+3]; cols=st.columns(3,gap="medium")
        for j,v in enumerate(batch):
            with cols[j]: _flota_card(v)

def _flota_card(v):
    est=v["estado"]
    ec={"Disponible":"#10B981","Ocupado":"#F43F5E","Mantenimiento":"#F59E0B"}.get(est,"#888")
    ti={"Grúa":"🏗️","Canasta":"🪣","Ligero":"🚐"}.get(v["tipo"],"🚗")
    zc=ZONA_COLOR.get(v["zona"],"#888")
    pct={"Disponible":100,"Ocupado":0,"Mantenimiento":50}.get(est,50)

    st.markdown(f"""<div class="card" style="border-left:3px solid {ec}">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:1.4rem">{ti}</span>
      <span style="color:{ec};font-weight:800;font-size:.8rem">{est}</span>
    </div>
    <div style="color:#E9B84A;font-weight:900;font-size:1rem;margin:4px 0">{v['id']}</div>
    <div style="color:#E2EEF9;font-size:.82rem;font-weight:600">👤 {v['chofer']}</div>
    <div style="color:{zc};font-size:.76rem;margin-top:2px">📍 {v['zona']} · {v['tipo']} · {v['capacidad_ton']}t</div>
    <div style="height:4px;background:rgba(255,255,255,.07);border-radius:2px;margin-top:10px">
      <div style="height:100%;width:{pct}%;background:{ec};border-radius:2px;transition:width .5s"></div>
    </div></div>""", unsafe_allow_html=True)

    # Editar estado rápido
    new_est=st.selectbox("Cambiar estado",["Disponible","Ocupado","Mantenimiento"],
        index=["Disponible","Ocupado","Mantenimiento"].index(est),
        key=f"sel_{v['id']}", label_visibility="collapsed")
    if new_est != est:
        if st.button(f"💾 {v['id']}", key=f"sv_{v['id']}"):
            db.update_estado_vehiculo(v["id"], new_est)
            st.success(f"✅ {v['id']} → {new_est}"); time.sleep(0.4); st.rerun()

    # Edición completa
    with st.expander("✏️ Editar", expanded=False):
        with st.form(f"edit_{v['id']}"):
            nch  = st.text_input("Chofer", value=v["chofer"])
            nt   = st.selectbox("Tipo",["Grúa","Canasta","Ligero"],
                                index=["Grúa","Canasta","Ligero"].index(v["tipo"]))
            nz   = st.selectbox("Zona", ZONAS, index=ZONAS.index(v["zona"]))
            nc   = st.number_input("Capacidad (t)", 0.5, 30.0, float(v["capacidad_ton"]), 0.5)
            saved = st.form_submit_button("💾 Guardar cambios")
        if saved:
            db.update_vehiculo(v["id"], {"chofer":nch.strip(),"tipo":nt,"zona":nz,"capacidad_ton":nc})
            st.success("✅ Actualizado."); time.sleep(0.4); st.rerun()

    # Eliminar
    if st.button(f"🗑️ Eliminar {v['id']}", key=f"del_{v['id']}", help="Eliminar vehículo de la flota"):
        if st.session_state.get(f"confirm_del_{v['id']}"):
            db.eliminar_vehiculo(v["id"])
            st.success(f"🗑️ {v['id']} eliminado."); time.sleep(0.4); st.rerun()
        else:
            st.session_state[f"confirm_del_{v['id']}"] = True
            st.warning("Vuelve a pulsar para confirmar eliminación.")


# ── Tab 6: Inventario de Taller ───────────────────────────────────────────────
def tab_inventario():
    stitle("📦 Control de Inventario del Taller")

    # KPIs
    inv = db.get_inventario()
    bajos = db.get_items_bajo_stock()
    cats = db.get_categorias_inventario()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Items", len(inv))
    c2.metric("Categorías", len(cats))
    c3.metric("⚠️ Stock Bajo", len(bajos))
    total_val = len([i for i in inv if i["cantidad"] > 0])
    c4.metric("Con Stock", total_val)

    if bajos:
        hdiv()
        st.error(f"⚠️ **{len(bajos)} ítem(s) con stock bajo o agotado** — requieren reabastecimiento urgente:")
        for b in bajos:
            nec = max(0, b["minimo_stock"] - b["cantidad"])
            st.markdown(f"  🔴 **{b['item']}** — {b['cantidad']} {b['unidad']} (mínimo: {b['minimo_stock']}, faltan: {nec})")

    hdiv()
    # ── Agregar ítem
    with st.expander("➕ Agregar Nuevo Ítem", expanded=False):
        with st.form("add_inv"):
            r1c1, r1c2, r1c3 = st.columns(3)
            nc   = r1c1.selectbox("Categoría",["EPP","Materiales Eléctricos","Herramientas","Repuestos","Consumibles","General"])
            ni   = r1c2.text_input("Nombre del ítem*", placeholder="Cable 14AWG")
            nun  = r1c3.text_input("Unidad", value="unidades")
            r2c1, r2c2, r2c3 = st.columns(3)
            ncant = r2c1.number_input("Cantidad inicial", 0.0, 99999.0, 0.0, 1.0)
            nmin  = r2c2.number_input("Stock mínimo", 0.0, 99999.0, 0.0, 1.0)
            nubi  = r2c3.text_input("Ubicación", placeholder="Bodega A1")
            nnot = st.text_input("Notas (opcional)")
            oka = st.form_submit_button("✅ Agregar al Inventario", use_container_width=True)
        if oka:
            if not ni.strip():
                st.error("El nombre del ítem es obligatorio.")
            else:
                db.agregar_item_inventario({"categoria":nc,"item":ni.strip(),"cantidad":ncant,
                                            "unidad":nun,"minimo_stock":nmin,"ubicacion":nubi,"notas":nnot})
                st.success(f"✅ '{ni}' agregado al inventario."); st.rerun()

    hdiv()
    # ── Filtros
    cf1, cf2, cf3 = st.columns([2,2,1])
    cat_sel = cf1.selectbox("Filtrar categoría", ["Todas"] + cats, key="inv_cat")
    buscar  = cf2.text_input("Buscar ítem", placeholder="Cable, casco...", key="inv_bus")
    solo_bajos = cf3.checkbox("Solo stock bajo", key="inv_bajo")

    datos = db.get_inventario(cat_sel if cat_sel != "Todas" else None)
    if buscar:
        datos = [d for d in datos if buscar.lower() in d["item"].lower()]
    if solo_bajos:
        datos = [d for d in datos if d["cantidad"] <= d["minimo_stock"] and d["minimo_stock"] > 0]

    stitle(f"Inventario ({len(datos)} items)")

    # ── Agrupado por categoría
    por_cat = {}
    for it in datos:
        por_cat.setdefault(it["categoria"], []).append(it)

    for cat, items in sorted(por_cat.items()):
        cat_icons = {"EPP":"🦺","Materiales Eléctricos":"⚡","Herramientas":"🔧","Repuestos":"🔩","Consumibles":"📋","General":"📦"}
        ico = cat_icons.get(cat, "📦")
        st.markdown(f'<div style="color:#E9B84A;font-weight:800;font-size:.9rem;margin:14px 0 8px;padding-bottom:4px;border-bottom:1px solid rgba(233,184,74,.2)">{ico} {cat} <span style="color:#3D5F7C;font-weight:400;font-size:.75rem">({len(items)} items)</span></div>', unsafe_allow_html=True)

        for it in items:
            pct_stock = min(100, int((it["cantidad"] / it["minimo_stock"] * 100)) if it["minimo_stock"] > 0 else 100)
            bar_c = "#F43F5E" if pct_stock <= 50 else "#F59E0B" if pct_stock <= 80 else "#10B981"
            is_low = it["cantidad"] <= it["minimo_stock"] and it["minimo_stock"] > 0
            
            with st.expander(f"{'⚠️' if is_low else '  '} {it['item']}  ·  {it['cantidad']} {it['unidad']}", expanded=is_low):
                col_info, col_adj, col_ed = st.columns([3,2,2])

                with col_info:
                    st.markdown(f"""
<div class="card" style="border-left:3px solid {bar_c};padding:10px 14px">
  <div style="color:#E2EEF9;font-weight:700">{it['item']}</div>
  <div style="color:#7A9BBC;font-size:.78rem">📍 {it.get('ubicacion','—')} · {it['unidad']}</div>
  <div style="color:#3D5F7C;font-size:.72rem">Mín: {it['minimo_stock']} {it['unidad']}</div>
  <div style="height:4px;background:rgba(255,255,255,.07);border-radius:2px;margin-top:8px">
    <div style="height:100%;width:{pct_stock}%;background:{bar_c};border-radius:2px"></div>
  </div>
</div>""", unsafe_allow_html=True)

                with col_adj:
                    st.markdown('<div style="color:#7A9BBC;font-size:.78rem;font-weight:700;margin-bottom:6px">🔄 Stock</div>', unsafe_allow_html=True)
                    delta = st.number_input("Cant",step=1.0,value=1.0,key=f"dlt_{it['id']}", label_visibility="collapsed")
                    c_ent, c_sal = st.columns(2)
                    if c_ent.button("➕ En",key=f"in_{it['id']}",use_container_width=True):
                        db.ajustar_cantidad(it["id"], delta); st.rerun()
                    if c_sal.button("➖ Sal",key=f"out_{it['id']}",use_container_width=True):
                        db.ajustar_cantidad(it["id"], -delta); st.rerun()

                with col_ed:
                    # Botón eliminar principal
                    if st.button("🗑️ Eliminar ítem", key=f"del_it_{it['id']}", use_container_width=True, help="Eliminar permanentemente"):
                        if st.session_state.get(f"crm_{it['id']}"):
                            db.eliminar_item_inventario(it["id"]); st.rerun()
                        else:
                            st.session_state[f"crm_{it['id']}"] = True
                            st.warning("Pulsa de nuevo para confirmar.")
                    
                    with st.expander("✏️ Editar Detalles"):
                        with st.form(f"upd_{it['id']}"):
                            nc2 = st.text_input("Nombre", value=it["item"])
                            nq2 = st.number_input("Cantidad", value=float(it["cantidad"]))
                            nm2 = st.number_input("Mínimo", 0.0, 1000.0, float(it["minimo_stock"]))
                            if st.form_submit_button("💾 Guardar"):
                                db.update_item_inventario(it["id"], {"item":nc2, "cantidad":nq2, "minimo_stock":nm2})
                                st.success("✅ Actualizado"); st.rerun()


    hdiv()
    if st.button("📥 Exportar Inventario CSV"):
        import pandas as pd
        df_exp = pd.DataFrame(inv)[["categoria","item","cantidad","unidad","minimo_stock","ubicacion","notas"]]
        st.download_button("⬇️ Descargar", df_exp.to_csv(index=False).encode(),
                           "inventario_taller.csv", "text/csv")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    sidebar()

    st.markdown(f"""<div class="hero">
    <h1>⚡ ElectroDispatch AI <span class="badge">{APP_VERSION}</span></h1>
    <p>Sistema Multi-Agente · 4 Agentes IA · 10 Zonas · 15 Vehículos · Bot: {BOT_USERNAME} · {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
    </div>""", unsafe_allow_html=True)

    t1,t2,t3,t4,t5,t6=st.tabs(["🏠 Dashboard","⚡ Despacho","📱 Telegram","📊 Estadísticas","🚛 Flota","📦 Inventario"])
    with t1: tab_dashboard()
    with t2: tab_despacho()
    with t3: tab_telegram()
    with t4: tab_estadisticas()
    with t5: tab_flota()
    with t6: tab_inventario()

if __name__=="__main__":
    main()
