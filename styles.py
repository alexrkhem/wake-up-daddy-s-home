import streamlit as st

def apply_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Space+Mono:wght@400;700&display=swap');

:root {
  --bg:       #1a1814;
  --surface:  #2d2520;
  --card:     #23201c;
  --cream:    #f0e6d3;
  --muted:    #9a8878;
  --orange:   #d4681e;
  --sage:     #7a8c6e;
  --gold:     #c4a882;
  --burgundy: #8b4049;
  --border:   #3d3028;
}

/* ── Base ─────────────────────────────────────────────── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, section.main {
  background-color: var(--bg) !important;
  color: var(--cream) !important;
  font-family: 'Space Mono', 'Courier New', monospace !important;
}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
  background-color: var(--surface) !important;
  border-right: 1px solid var(--gold) !important;
}
[data-testid="stSidebar"] * { color: var(--cream) !important; }

/* ── Typography ───────────────────────────────────────── */
h1, h2, h3, h4 {
  font-family: 'Playfair Display', Georgia, serif !important;
  letter-spacing: 0.02em;
}
h1 { color: var(--gold) !important; font-size: 2rem !important; }
h2 { color: var(--cream) !important; }
h3 { color: var(--orange) !important; font-size: 1.1rem !important; }
p, li, label, span { color: var(--cream) !important; }
.stMarkdown { color: var(--cream) !important; }

/* ── Metrics ──────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--orange) !important;
  border-radius: 4px !important;
  padding: 0.8rem 1rem !important;
}
[data-testid="stMetricValue"] {
  color: var(--orange) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 1.6rem !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 1px; }
[data-testid="stMetricDelta"] { font-family: 'Space Mono', monospace !important; }

/* ── Buttons ──────────────────────────────────────────── */
.stButton > button {
  background: var(--orange) !important;
  color: var(--bg) !important;
  border: none !important;
  font-family: 'Space Mono', monospace !important;
  font-weight: 700 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  font-size: 0.72rem !important;
  padding: 0.45rem 1.1rem !important;
  border-radius: 2px !important;
  transition: all 0.15s ease !important;
}
.stButton > button:hover {
  background: var(--gold) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(196,168,130,0.3) !important;
}

/* ── Inputs ───────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea textarea,
.stNumberInput > div > div > input,
.stDateInput input,
.stTimeInput input,
.stSelectbox > div > div {
  background: var(--surface) !important;
  color: var(--cream) !important;
  border: 1px solid var(--border) !important;
  border-radius: 3px !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 0.85rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
  border-color: var(--orange) !important;
  box-shadow: 0 0 0 1px var(--orange) !important;
}
.stSelectbox > div { background: var(--surface) !important; }
.stSelectbox svg { fill: var(--muted) !important; }

/* ── Tabs ─────────────────────────────────────────────── */
[data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}
[data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 0.72rem !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  border-bottom: 2px solid transparent !important;
}
[data-baseweb="tab"][aria-selected="true"] {
  color: var(--orange) !important;
  border-bottom-color: var(--orange) !important;
  background: transparent !important;
}
[data-baseweb="tab-panel"] { background: var(--bg) !important; padding-top: 1rem !important; }

/* ── Expanders ────────────────────────────────────────── */
details > summary,
[data-testid="stExpander"] > div:first-child {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--cream) !important;
  font-family: 'Space Mono', monospace !important;
  border-radius: 3px !important;
}
[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 4px !important; }

/* ── Dataframes ───────────────────────────────────────── */
[data-testid="stDataFrame"], .dataframe {
  background: var(--surface) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 0.8rem !important;
}

/* ── Chat ─────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  margin-bottom: 0.5rem !important;
}
.stChatInputContainer, [data-testid="stChatInput"] {
  background: var(--surface) !important;
  border-top: 1px solid var(--border) !important;
}
[data-testid="stChatInput"] textarea {
  background: var(--surface) !important;
  color: var(--cream) !important;
  font-family: 'Space Mono', monospace !important;
}

/* ── Progress / Sliders ───────────────────────────────── */
.stProgress > div > div { background: var(--orange) !important; }
.stSlider > div > div > div { background: var(--orange) !important; }

/* ── Checkboxes ───────────────────────────────────────── */
[data-baseweb="checkbox"] > div { background: var(--surface) !important; border-color: var(--gold) !important; }
[data-baseweb="checkbox"][data-checked="true"] > div { background: var(--orange) !important; border-color: var(--orange) !important; }

/* ── Alerts ───────────────────────────────────────────── */
[data-testid="stSuccess"] { background: rgba(122,140,110,0.15) !important; border-color: var(--sage) !important; border-radius: 3px !important; }
[data-testid="stError"]   { background: rgba(139,64,73,0.15) !important; border-color: var(--burgundy) !important; border-radius: 3px !important; }
[data-testid="stInfo"]    { background: rgba(196,168,130,0.1) !important; border-color: var(--gold) !important; border-radius: 3px !important; }
[data-testid="stWarning"] { background: rgba(212,104,30,0.12) !important; border-color: var(--orange) !important; border-radius: 3px !important; }

/* ── File Uploader ────────────────────────────────────── */
[data-testid="stFileUploader"] {
  background: var(--card) !important;
  border: 1.5px dashed var(--gold) !important;
  border-radius: 4px !important;
}

/* ── Scrollbar ────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ── Custom Components ────────────────────────────────── */
.vinyl-card {
  background: var(--surface);
  border-left: 3px solid var(--orange);
  padding: 0.9rem 1.2rem;
  margin: 0.4rem 0;
  border-radius: 0 4px 4px 0;
}
.vinyl-card-sage  { border-left-color: var(--sage) !important; }
.vinyl-card-gold  { border-left-color: var(--gold) !important; }
.vinyl-card-burg  { border-left-color: var(--burgundy) !important; }

.label-mono {
  font-family: 'Space Mono', monospace;
  font-size: 0.68rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 0.2rem;
}
.track-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.3rem;
  color: var(--cream);
  margin: 0;
}
.vinyl-divider {
  height: 1px;
  background: linear-gradient(to right, transparent, var(--gold), transparent);
  margin: 1.5rem 0;
  border: none;
}
.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 2px;
  font-family: 'Space Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  font-weight: 700;
}
.badge-high    { background: rgba(139,64,73,0.3); color: #e08090; border: 1px solid var(--burgundy); }
.badge-medium  { background: rgba(212,104,30,0.2); color: var(--orange); border: 1px solid var(--orange); }
.badge-low     { background: rgba(122,140,110,0.2); color: var(--sage); border: 1px solid var(--sage); }
.badge-done    { background: rgba(122,140,110,0.15); color: var(--sage); border: 1px solid var(--sage); }
.badge-todo    { background: rgba(154,136,120,0.15); color: var(--muted); border: 1px solid var(--muted); }
.badge-inprog  { background: rgba(212,104,30,0.15); color: var(--orange); border: 1px solid var(--orange); }
.badge-gold    { background: rgba(196,168,130,0.15); color: var(--gold); border: 1px solid var(--gold); }

.win-streak-number {
  font-family: 'Playfair Display', serif;
  font-size: 3.5rem;
  color: var(--gold);
  line-height: 1;
}
.stat-row { display: flex; justify-content: space-between; align-items: center; padding: 0.3rem 0; }
.stat-label { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; }
.stat-val   { color: var(--cream); font-size: 0.9rem; font-family: 'Space Mono', monospace; }

.overdue { color: var(--burgundy) !important; }

/* Remove Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

def page_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"""
<div style="padding:1rem 0 0.5rem;">
  <div class="label-mono">{icon} {subtitle if subtitle else "dashboard"}</div>
  <div class="track-title">{title}</div>
  <div class="vinyl-divider"></div>
</div>""", unsafe_allow_html=True)

def vinyl_card(content_html: str, variant: str = ""):
    cls = f"vinyl-card {variant}"
    st.markdown(f'<div class="{cls}">{content_html}</div>', unsafe_allow_html=True)

def badge(text: str, kind: str = "medium") -> str:
    return f'<span class="badge badge-{kind}">{text}</span>'
