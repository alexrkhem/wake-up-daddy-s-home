import streamlit as st, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Music · Jarvis", page_icon="🎵", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
import plotly.graph_objects as go
init_db(); apply_styles(); render_jarvis_sidebar()

conn  = get_connection()
today = datetime.date.today()
def run_q(sql,p=()): conn.execute(sql,p); conn.commit()
def get_q(sql,p=()): c=conn.cursor(); c.execute(sql,p); return c.fetchall()
def get1(sql,p=()):  c=conn.cursor(); c.execute(sql,p); r=c.fetchone(); return r

GUITAR_CATS    = ["Technique","Songs/Repertoire","Music Theory","Improvisation","Sight-Reading","Ear Training","Composition","Other"]
EUPHONIUM_CATS = ["Scales & Long Tones","Etudes","Repertoire","Sight-Reading","Breathing Technique","Theory","Ensemble Prep","Other"]

page_header("🎵", "Music Practice Tracker", "guitar · euphonium · consistency")

# ── Stats ────────────────────────────────────────────────────────────────────
wk_ago = str(today - datetime.timedelta(days=7))
mo_ago = str(today - datetime.timedelta(days=30))

for_inst = lambda inst, since: get1("SELECT COALESCE(SUM(duration_mins),0) FROM music_sessions WHERE instrument=? AND date>=?", (inst, since))

g_wk  = for_inst("guitar",    wk_ago)[0]; g_mo  = for_inst("guitar",    mo_ago)[0]
e_wk  = for_inst("euphonium", wk_ago)[0]; e_mo  = for_inst("euphonium", mo_ago)[0]
total_sessions = get1("SELECT COUNT(*) FROM music_sessions")[0]

# streak
streak = 0
for i in range(60):
    d = str(today - datetime.timedelta(days=i))
    if get1("SELECT COUNT(*) FROM music_sessions WHERE date=?", (d,))[0]: streak += 1
    elif i > 0: break

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Practice Streak", f"{streak}d")
c2.metric("Guitar / 7d",     f"{g_wk//60}h {g_wk%60}m")
c3.metric("Guitar / 30d",    f"{g_mo//60}h {g_mo%60}m")
c4.metric("Euphonium / 7d",  f"{e_wk//60}h {e_wk%60}m")
c5.metric("Total Sessions",  total_sessions)

st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)

tab_guitar, tab_euph, tab_goals, tab_stats = st.tabs(["🎸 Guitar", "🎺 Euphonium", "🎯 Goals", "📊 Stats"])

def session_log_form(instrument, categories, form_key):
    with st.form(form_key):
        fc1,fc2,fc3 = st.columns(3)
        with fc1:
            s_date  = st.date_input("Date", value=today, key=f"d_{form_key}")
            s_cat   = st.selectbox("Category", categories, key=f"cat_{form_key}")
        with fc2:
            s_dur   = st.number_input("Duration (min)", 5, 480, 30, 5, key=f"dur_{form_key}")
            s_qual  = st.slider("Session Quality", 1, 5, 3, key=f"q_{form_key}")
        with fc3:
            s_bpm   = st.number_input("BPM Practiced (0=N/A)", 0, 300, 0, 5, key=f"bpm_{form_key}")
            s_piece = st.text_input("Piece / Exercise", key=f"pc_{form_key}")
        s_notes = st.text_area("Notes", height=68, key=f"n_{form_key}")
        if st.form_submit_button(f"Log {instrument.title()} Session"):
            run_q("""INSERT INTO music_sessions (date,instrument,category,duration_mins,quality,bpm_practiced,piece_worked_on,notes)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (str(s_date), instrument, s_cat, s_dur, s_qual, s_bpm if s_bpm else None, s_piece.strip(), s_notes.strip()))
            st.success(f"Logged {s_dur}min {instrument} — {s_cat}!"); st.rerun()

def session_history(instrument, limit=20):
    sessions = get_q("""SELECT id,date,category,duration_mins,quality,piece_worked_on,notes,bpm_practiced
                        FROM music_sessions WHERE instrument=?
                        ORDER BY date DESC, id DESC LIMIT ?""", (instrument, limit))
    if not sessions:
        st.info(f"No {instrument} sessions logged yet."); return

    qual_colors = {1:"#8b4049",2:"#d4681e",3:"#c4a882",4:"#7a8c6e",5:"#f0e6d3"}
    for s in sessions:
        sid, sdate, scat, sdur, squal, spiece, snotes, sbpm = s
        qc  = qual_colors.get(squal, "#9a8878")
        bpm_html = f' <span style="color:#9a8878;font-size:.65rem">@ {sbpm} BPM</span>' if sbpm else ""
        piece_html = f'<span style="color:#c4a882">{spiece}</span>' if spiece else ""
        st.markdown(f"""
<div class="vinyl-card" style="padding:.45rem 1rem;margin:.2rem 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span style="font-size:.82rem;color:#f0e6d3">{scat}</span>
      {f' — {piece_html}' if spiece else ''}{bpm_html}
    </div>
    <div style="text-align:right">
      <span style="font-family:'Space Mono',monospace;font-size:.8rem;color:#d4681e">{sdur}min</span>
      &nbsp;
      <span style="font-size:.75rem;color:{qc}">{'★'*squal}{'☆'*(5-squal)}</span>
    </div>
  </div>
  <div style="font-size:.65rem;color:#9a8878;margin-top:.15rem">{sdate}{f' · {snotes[:80]}' if snotes else ''}</div>
</div>""", unsafe_allow_html=True)

with tab_guitar:
    session_log_form("guitar", GUITAR_CATS, "gform")
    st.markdown("### Recent Sessions")
    session_history("guitar")

with tab_euph:
    session_log_form("euphonium", EUPHONIUM_CATS, "eform")
    st.markdown("### Recent Sessions")
    session_history("euphonium")

with tab_goals:
    st.markdown("### 🎯 Music Goals")
    goals = get_q("""SELECT id,instrument,goal_text,target_date,achieved FROM music_goals
                     ORDER BY achieved, target_date""")
    for g in goals:
        gid, ginst, gtxt, gtdate, gach = g
        color  = "#7a8c6e" if gach else "#d4681e"
        strike = "text-decoration:line-through;opacity:.5;" if gach else ""
        past   = gtdate and gtdate < str(today) and not gach
        past_tag = ' <span style="color:#8b4049;font-size:.65rem">PAST DUE</span>' if past else ""
        col_a, col_b = st.columns([5,1])
        with col_a:
            st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{color};padding:.45rem 1rem;margin:.2rem 0">
  <div style="font-size:.85rem;{strike}">{ginst.title()} — {gtxt}</div>
  <div style="font-size:.65rem;color:#9a8878">Target: {gtdate or 'No date'}{past_tag}</div>
</div>""", unsafe_allow_html=True)
        with col_b:
            st.markdown('<div style="height:.3rem"></div>', unsafe_allow_html=True)
            if st.button("✓" if not gach else "↺", key=f"gach_{gid}"):
                run_q("UPDATE music_goals SET achieved=? WHERE id=?", (0 if gach else 1, gid)); st.rerun()

    with st.form("add_goal"):
        gc1,gc2,gc3 = st.columns(3)
        with gc1: g_inst  = st.selectbox("Instrument", ["guitar","euphonium"])
        with gc2: g_text  = st.text_input("Goal")
        with gc3: g_tdate = st.date_input("Target Date", value=None)
        if st.form_submit_button("Add Goal"):
            if g_text.strip():
                run_q("INSERT INTO music_goals (instrument,goal_text,target_date) VALUES (?,?,?)",
                      (g_inst, g_text.strip(), str(g_tdate) if g_tdate else None))
                st.rerun()

with tab_stats:
    # Time by category — guitar
    for inst, cats in [("guitar", GUITAR_CATS), ("euphonium", EUPHONIUM_CATS)]:
        cat_data = get_q("""SELECT category, SUM(duration_mins) FROM music_sessions
                            WHERE instrument=? AND date>=? GROUP BY category ORDER BY 2 DESC""",
                         (inst, mo_ago))
        if cat_data:
            st.markdown(f'<div style="font-family:Playfair Display,serif;font-size:1.05rem;color:#c4a882;margin:.8rem 0 .3rem">{inst.title()} — Category Breakdown (30d)</div>', unsafe_allow_html=True)
            fig = go.Figure(go.Bar(
                x=[r[1] for r in cat_data], y=[r[0] for r in cat_data],
                orientation="h", marker_color="#d4681e" if inst=="guitar" else "#c4a882",
                marker_line_width=0))
            fig.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                              font=dict(color="#f0e6d3", family="Space Mono"),
                              xaxis=dict(title="Minutes", gridcolor="#2d2520"),
                              yaxis=dict(color="#9a8878"),
                              margin=dict(l=10,r=10,t=10,b=10), height=200)
            st.plotly_chart(fig, use_container_width=True)

    # Calendar heat map proxy
    all_sessions = get_q("""SELECT date, SUM(duration_mins) FROM music_sessions
                            WHERE date>=? GROUP BY date ORDER BY date""",
                         (str(today - datetime.timedelta(days=60)),))
    if len(all_sessions) >= 3:
        fig3 = go.Figure(go.Scatter(
            x=[r[0] for r in all_sessions], y=[r[1] for r in all_sessions],
            mode="markers+lines", marker=dict(size=8, color=[r[1] for r in all_sessions],
                                              colorscale=[[0,"#2d2520"],[0.5,"#d4681e"],[1,"#c4a882"]],
                                              showscale=False),
            line=dict(color="#3d3028", width=1)))
        fig3.add_hline(y=30, line_dash="dot", line_color="#7a8c6e", opacity=0.5,
                       annotation_text="30min/day goal")
        fig3.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                           font=dict(color="#f0e6d3", family="Space Mono"),
                           yaxis=dict(title="Minutes", gridcolor="#2d2520"),
                           xaxis=dict(color="#9a8878"),
                           margin=dict(l=10,r=10,t=10,b=10), height=220,
                           title=dict(text="Daily Practice Minutes (60d)", font=dict(color="#c4a882")))
        st.plotly_chart(fig3, use_container_width=True)

conn.close()
