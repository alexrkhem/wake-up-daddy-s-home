import streamlit as st, sys, datetime, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Sleep · Jarvis", page_icon="😴", layout="wide")
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

page_header("😴", "Sleep Tracker", "rest & recovery")

# ── Stats Row ────────────────────────────────────────────────────────────────
last7  = get_q("SELECT duration_hours,quality,routine_followed FROM sleep_log ORDER BY date DESC LIMIT 7")
avg_h  = sum(r[0] for r in last7 if r[0])/max(len([r for r in last7 if r[0]]),1)
avg_q  = sum(r[1] for r in last7 if r[1])/max(len([r for r in last7 if r[1]]),1)
streak = sum(1 for r in last7 if r[2])

c1,c2,c3,c4 = st.columns(4)
c1.metric("Avg Sleep (7d)", f"{avg_h:.1f}h",  "Goal: 8h")
c2.metric("Avg Quality (7d)", f"{avg_q:.1f}/10")
c3.metric("Routine Streak", f"{streak}d",      "last 7 days")
debt = max(0, round((8 - avg_h) * 7, 1))
c4.metric("Sleep Debt (wk)", f"{debt}h", delta_color="inverse")

st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)

tab_log, tab_chart, tab_routine = st.tabs(["📝  Log Sleep", "📊  Charts", "🌙  Routine Checklist"])

with tab_log:
    existing = get1("SELECT bedtime,wake_time,quality,notes,routine_followed FROM sleep_log WHERE date=?", (str(today),))
    st.markdown(f'<div class="label-mono">Logging for {today.strftime("%A, %B %-d, %Y")}</div>', unsafe_allow_html=True)

    with st.form("sleep_form"):
        c1,c2,c3 = st.columns(3)
        with c1:
            log_date = st.date_input("Date", value=today)
            bedtime  = st.time_input("Bedtime", value=datetime.time(22,30) if not existing else datetime.time(*map(int,existing[0].split(":"))) if existing[0] else datetime.time(22,30))
        with c2:
            wake_time = st.time_input("Wake Time", value=datetime.time(6,30) if not existing else datetime.time(*map(int,existing[1].split(":"))) if existing[1] else datetime.time(6,30))
            quality   = st.slider("Quality", 1, 10, int(existing[2]) if existing and existing[2] else 7)
        with c3:
            routine_done = st.checkbox("Completed sleep routine?", value=bool(existing[4]) if existing else False)
            notes = st.text_area("Notes", value=existing[3] if existing and existing[3] else "", height=80)

        # Calculate duration
        bed_dt  = datetime.datetime.combine(log_date - datetime.timedelta(days=1 if bedtime > wake_time else 0), bedtime)
        wake_dt = datetime.datetime.combine(log_date, wake_time)
        duration = round((wake_dt - bed_dt).seconds / 3600, 2)

        if st.form_submit_button("Save Sleep Log"):
            run_q("""INSERT INTO sleep_log (date,bedtime,wake_time,duration_hours,quality,notes,routine_followed)
                     VALUES (?,?,?,?,?,?,?)
                     ON CONFLICT(date) DO UPDATE SET bedtime=excluded.bedtime,wake_time=excluded.wake_time,
                     duration_hours=excluded.duration_hours,quality=excluded.quality,
                     notes=excluded.notes,routine_followed=excluded.routine_followed""",
                  (str(log_date), str(bedtime)[:5], str(wake_time)[:5], duration, quality, notes, int(routine_done)))
            st.success(f"Logged {duration}h sleep for {log_date}!"); st.rerun()

    # Recent log
    st.markdown("### Recent Sleep Log")
    recent = get_q("SELECT date,bedtime,wake_time,duration_hours,quality,routine_followed FROM sleep_log ORDER BY date DESC LIMIT 14")
    if recent:
        for r in recent:
            q_color = "#7a8c6e" if (r[4] or 0)>=7 else "#d4681e" if (r[4] or 0)>=5 else "#8b4049"
            h_color = "#7a8c6e" if (r[3] or 0)>=7.5 else "#d4681e" if (r[3] or 0)>=6 else "#8b4049"
            rout_ico = "✓" if r[5] else "✗"
            rout_c   = "#7a8c6e" if r[5] else "#8b4049"
            st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
padding:.3rem .8rem;background:#23201c;border-radius:3px;margin:.15rem 0;font-size:.78rem">
<span style="color:#9a8878;width:90px">{r[0]}</span>
<span style="color:#9a8878">{r[1] or '—'} → {r[2] or '—'}</span>
<span style="color:{h_color};font-family:'Space Mono',monospace">{r[3] or 0:.1f}h</span>
<span style="color:{q_color}">Q:{r[4] or '—'}</span>
<span style="color:{rout_c}">{rout_ico}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.info("No sleep data yet.")

with tab_chart:
    data30 = get_q("SELECT date,duration_hours,quality FROM sleep_log ORDER BY date DESC LIMIT 30")
    if len(data30) >= 2:
        data30 = list(reversed(data30))
        dates  = [r[0] for r in data30]
        hours  = [r[1] or 0 for r in data30]
        quals  = [r[2] or 0 for r in data30]

        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=hours, name="Hours", marker_color="#d4681e",
                             marker_line_width=0, opacity=0.85))
        fig.add_trace(go.Scatter(x=dates, y=quals, name="Quality", yaxis="y2",
                                 line=dict(color="#c4a882", width=2), mode="lines+markers",
                                 marker=dict(size=5)))
        fig.add_hline(y=8, line_dash="dash", line_color="#7a8c6e", opacity=0.5,
                      annotation_text="8h goal", annotation_font_color="#7a8c6e")
        fig.update_layout(
            paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
            font=dict(color="#f0e6d3", family="Space Mono"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            yaxis=dict(title="Hours", color="#f0e6d3", gridcolor="#2d2520"),
            yaxis2=dict(title="Quality", overlaying="y", side="right",
                        range=[0,10], color="#c4a882", gridcolor="rgba(0,0,0,0)"),
            xaxis=dict(color="#9a8878", gridcolor="#2d2520"),
            margin=dict(l=10,r=10,t=10,b=10), height=320
        )
        st.plotly_chart(fig, use_container_width=True)

        # Bedtime consistency
        bedtimes = get_q("SELECT date,bedtime FROM sleep_log WHERE bedtime IS NOT NULL ORDER BY date DESC LIMIT 21")
        if len(bedtimes) >= 3:
            def to_hour(t):
                try:
                    h,m = map(int, t.split(":")); return h + m/60 + (24 if h<12 else 0)
                except: return None
            bts = [(r[0], to_hour(r[1])) for r in reversed(bedtimes) if r[1]]
            bts = [(d,h) for d,h in bts if h]
            if bts:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=[b[0] for b in bts], y=[b[1] for b in bts],
                    mode="lines+markers", line=dict(color="#7a8c6e", width=2),
                    marker=dict(size=6, color="#7a8c6e"), name="Bedtime (hr)"
                ))
                fig2.add_hline(y=22.5, line_dash="dash", line_color="#d4681e", opacity=0.5,
                               annotation_text="10:30pm target")
                fig2.update_layout(
                    paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                    font=dict(color="#f0e6d3", family="Space Mono"),
                    yaxis=dict(title="Hour (24h)", color="#f0e6d3", gridcolor="#2d2520",
                               tickvals=[21,22,23,24,25], ticktext=["9pm","10pm","11pm","12am","1am"]),
                    xaxis=dict(color="#9a8878", gridcolor="#2d2520"),
                    margin=dict(l=10,r=10,t=20,b=10), height=220,
                    title=dict(text="Bedtime Consistency", font=dict(color="#c4a882"))
                )
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Log at least 2 nights to see charts.")

with tab_routine:
    st.markdown("### 🌙 Pre-Sleep Routine")
    st.markdown('<div style="font-size:.8rem;color:#9a8878;margin-bottom:1rem">Check off steps you\'ve completed tonight. Saves with your sleep log.</div>', unsafe_allow_html=True)

    routine_steps = get_q("SELECT id,step_order,activity,time_before_sleep,active FROM sleep_routine ORDER BY step_order")

    if "routine_checks" not in st.session_state:
        st.session_state.routine_checks = {}

    all_checked = True
    for step in routine_steps:
        sid, order, activity, timing, active = step
        if not active: continue
        key    = f"routine_{sid}"
        checked = st.checkbox(f"**{activity}**  —  _{timing}_", key=key)
        if not checked: all_checked = False

    if all_checked and routine_steps:
        st.success("🌙 Full routine complete — great consistency!")

    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ✏️ Edit Routine")
    with st.form("add_routine_step"):
        c1,c2 = st.columns(2)
        with c1: new_activity = st.text_input("New Activity")
        with c2: new_timing   = st.text_input("When", placeholder="e.g. 30 mins before")
        if st.form_submit_button("Add Step"):
            if new_activity.strip():
                max_order = get1("SELECT MAX(step_order) FROM sleep_routine")
                next_order = (max_order[0] or 0) + 1 if max_order else 1
                run_q("INSERT INTO sleep_routine (step_order,activity,time_before_sleep) VALUES (?,?,?)",
                      (next_order, new_activity.strip(), new_timing.strip()))
                st.rerun()

conn.close()
