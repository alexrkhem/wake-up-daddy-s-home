import streamlit as st, sys, datetime, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Fitness · Jarvis", page_icon="💪", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
from config import PHOTOS_DIR
import plotly.graph_objects as go
from PIL import Image
import io
init_db(); apply_styles(); render_jarvis_sidebar()

conn  = get_connection()
today = datetime.date.today()
def run_q(sql,p=()): conn.execute(sql,p); conn.commit()
def get_q(sql,p=()): c=conn.cursor(); c.execute(sql,p); return c.fetchall()
def get1(sql,p=()):  c=conn.cursor(); c.execute(sql,p); r=c.fetchone(); return r

page_header("💪", "Fitness Tracker", "weightlifting · steps · physique")

tab_lift, tab_steps, tab_height, tab_photos, tab_supps = st.tabs([
    "🏋️ Lifting", "👟 Steps", "📏 Height Training", "📸 Physique", "💊 Supplements"])

# ═══════════════════════ LIFTING ════════════════════════════════════════════
with tab_lift:
    c1,c2,c3 = st.columns(3)
    wk_ago   = str(today - datetime.timedelta(days=7))
    c1.metric("Workouts (7d)", get1("SELECT COUNT(*) FROM workouts WHERE date>=?",(wk_ago,))[0])
    c2.metric("Workouts (30d)", get1("SELECT COUNT(*) FROM workouts WHERE date>=?",
                                     (str(today-datetime.timedelta(days=30)),))[0])
    total_w  = get1("SELECT COUNT(*) FROM workouts")[0]
    c3.metric("All-Time Sessions", total_w)

    with st.expander("＋  Log New Workout", expanded=True):
        with st.form("log_workout"):
            wc1,wc2,wc3 = st.columns(3)
            with wc1:
                w_date     = st.date_input("Date", value=today)
                w_location = st.selectbox("Location", ["gym","home"])
            with wc2:
                w_name    = st.text_input("Workout Name", placeholder="e.g. Push A, Pull B")
                w_dur     = st.number_input("Duration (mins)", 15, 300, 60, 5)
            with wc3:
                w_notes   = st.text_area("Notes", height=68)

            st.markdown('<div class="label-mono" style="margin-top:.5rem">Exercises</div>', unsafe_allow_html=True)
            exercises = []
            for i in range(1, 8):
                ec1,ec2,ec3,ec4,ec5 = st.columns([2.5,0.8,0.8,0.8,1.5])
                with ec1: ex_name   = st.text_input(f"Exercise {i}", key=f"exname{i}", label_visibility="collapsed", placeholder=f"Exercise {i}")
                with ec2: ex_sets   = st.number_input("Sets",  1, 20, 3, key=f"sets{i}", label_visibility="collapsed")
                with ec3: ex_reps   = st.text_input("Reps",  key=f"reps{i}", label_visibility="collapsed", placeholder="Reps")
                with ec4: ex_weight = st.number_input("lbs",  0.0, 1000.0, 0.0, 2.5, key=f"wt{i}", label_visibility="collapsed")
                with ec5: ex_note   = st.text_input("Note",  key=f"enote{i}", label_visibility="collapsed", placeholder="Note")
                if ex_name.strip():
                    exercises.append((ex_name.strip(), ex_sets, ex_reps.strip(), ex_weight, ex_note.strip()))

            if st.form_submit_button("Save Workout"):
                if exercises or w_name.strip():
                    run_q("INSERT INTO workouts (date,location,name,duration_mins,notes) VALUES (?,?,?,?,?)",
                          (str(w_date), w_location, w_name.strip(), w_dur, w_notes.strip()))
                    wid = get1("SELECT last_insert_rowid()")[0]
                    for ex in exercises:
                        run_q("INSERT INTO workout_exercises (workout_id,name,sets,reps,weight_lbs,notes) VALUES (?,?,?,?,?,?)",
                              (wid, *ex))
                    st.success("Workout saved!"); st.rerun()
                else:
                    st.error("Add at least one exercise or a workout name.")

    # Recent workouts
    st.markdown("### Recent Workouts")
    recent_w = get_q("SELECT id,date,location,name,duration_mins FROM workouts ORDER BY date DESC LIMIT 20")
    for w in recent_w:
        wid, wdate, wloc, wname, wdur = w
        exercises_w = get_q("SELECT name,sets,reps,weight_lbs FROM workout_exercises WHERE workout_id=?", (wid,))
        loc_ico  = "🏋️" if wloc == "gym" else "🏠"
        with st.expander(f"{loc_ico} {wdate} — {wname or 'Workout'} ({wdur} min)"):
            if exercises_w:
                for ex in exercises_w:
                    wt_str = f" @ {ex[3]:.1f}lbs" if ex[3] else ""
                    st.markdown(f'<div style="font-size:.82rem;padding:.15rem 0;color:#f0e6d3">'
                                f'<span style="color:#d4681e">▸</span> '
                                f'<span style="font-weight:700">{ex[0]}</span> — {ex[1]}×{ex[2] or "?"}{wt_str}</div>',
                                unsafe_allow_html=True)
            else:
                st.markdown('<span style="color:#9a8878;font-size:.8rem">No exercises logged.</span>', unsafe_allow_html=True)
            if st.button("🗑 Delete", key=f"delw_{wid}"):
                run_q("DELETE FROM workouts WHERE id=?", (wid,)); st.rerun()

    # Volume chart
    vol_data = get_q("""SELECT date, SUM(sets * CAST(REPLACE(reps,'?','0') AS INTEGER) * weight_lbs)
                        FROM workouts w JOIN workout_exercises e ON w.id=e.workout_id
                        WHERE w.date>=? GROUP BY w.date ORDER BY w.date""",
                     (str(today - datetime.timedelta(days=30)),))
    if len(vol_data) >= 3:
        fig = go.Figure(go.Bar(
            x=[r[0] for r in vol_data], y=[r[1] or 0 for r in vol_data],
            marker_color="#d4681e", marker_line_width=0))
        fig.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                          font=dict(color="#f0e6d3", family="Space Mono"),
                          yaxis=dict(title="Volume (lbs)", gridcolor="#2d2520"),
                          xaxis=dict(color="#9a8878", gridcolor="#2d2520"),
                          margin=dict(l=10,r=10,t=20,b=10), height=220,
                          title=dict(text="Training Volume — 30 Days", font=dict(color="#c4a882")))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════ STEPS ══════════════════════════════════════════════
with tab_steps:
    with st.form("log_steps"):
        sc1,sc2,sc3 = st.columns(3)
        with sc1: s_date = st.date_input("Date", value=today)
        with sc2: s_steps = st.number_input("Steps", 0, 100000, 8000, 500)
        with sc3: s_goal  = st.number_input("Goal", 5000, 30000, 10000, 1000)
        if st.form_submit_button("Log Steps"):
            run_q("INSERT INTO steps_log (date,steps,goal) VALUES (?,?,?) ON CONFLICT(date) DO UPDATE SET steps=excluded.steps,goal=excluded.goal",
                  (str(s_date), s_steps, s_goal))
            st.success(f"Logged {s_steps:,} steps!"); st.rerun()

    steps14 = get_q("SELECT date,steps,goal FROM steps_log ORDER BY date DESC LIMIT 14")
    if steps14:
        steps14 = list(reversed(steps14))
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[r[0] for r in steps14], y=[r[1] for r in steps14],
                             name="Steps", marker_color="#7a8c6e", marker_line_width=0))
        goal_line = steps14[-1][2] if steps14 else 10000
        fig.add_hline(y=goal_line, line_dash="dash", line_color="#d4681e",
                      annotation_text=f"Goal: {goal_line:,}")
        fig.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                          font=dict(color="#f0e6d3", family="Space Mono"),
                          yaxis=dict(gridcolor="#2d2520"), xaxis=dict(color="#9a8878"),
                          margin=dict(l=10,r=10,t=10,b=10), height=250)
        st.plotly_chart(fig, use_container_width=True)
        for r in reversed(steps14[-7:]):
            pct = min(int(r[1]/(r[2] or 10000)*100),100)
            color = "#7a8c6e" if r[1]>=(r[2] or 10000) else "#d4681e"
            st.markdown(f"""<div style="display:flex;align-items:center;gap:1rem;margin:.2rem 0;font-size:.78rem">
<span style="color:#9a8878;width:95px">{r[0]}</span>
<div style="flex:1;background:#2d2520;border-radius:2px;height:6px">
  <div style="background:{color};width:{pct}%;height:6px;border-radius:2px"></div></div>
<span style="color:{color};font-family:'Space Mono',monospace;width:60px">{r[1]:,}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.info("No step data yet.")

# ═══════════════════════ HEIGHT TRAINING ════════════════════════════════════
with tab_height:
    st.markdown("### 📏 Height Maximization Training Protocol")
    st.markdown('<div style="font-size:.8rem;color:#9a8878;margin-bottom:1rem">Based on spinal decompression, posture, and growth-plate stimulation principles. Consistency is everything.</div>', unsafe_allow_html=True)

    routines = {
        "Morning Activation (15 min)": [
            ("Hanging Dead Hang", "3×60 sec", "Full spinal decompression — passive hang"),
            ("Cat-Cow Stretch", "3×20 reps", "Thoracic & lumbar mobility"),
            ("Child's Pose to Cobra", "3×30 sec each", "Full spine extension"),
            ("Ankle Hops", "3×30 reps", "Light loading for tibia"),
        ],
        "Jumping Protocol (Alternate Days)": [
            ("Box Jumps", "5×10", "Explosive vertical — max height"),
            ("Standing Broad Jump", "5×8", "Full-body explosive extension"),
            ("Jump Rope", "3×3 min", "Tibial loading + coordination"),
            ("Calf Raises — Single Leg", "3×20", "Bone density stimulus"),
        ],
        "Evening Decompression (10 min)": [
            ("Inversion Table / Hang", "2×90 sec", "Post-day spinal rehydration"),
            ("Spinal Twist — Supine", "2×60 sec/side", "Rotational mobility"),
            ("Legs-Up-The-Wall", "5 min", "Circulation + relaxation"),
        ],
        "Posture Correction (Daily)": [
            ("Wall Angels", "3×15", "Scapular retraction + thoracic extension"),
            ("Chin Tucks", "4×15", "Forward-head posture correction"),
            ("Thoracic Extension on Foam Roller", "2×60 sec", "Kyphosis reduction"),
            ("Hip Flexor Stretch", "3×60 sec/side", "Anterior pelvic tilt correction"),
        ]
    }

    for block_name, exercises in routines.items():
        st.markdown(f'<div style="font-family:Playfair Display,serif;font-size:1.05rem;color:#c4a882;margin:1rem 0 .4rem">{block_name}</div>', unsafe_allow_html=True)
        for ex_name, sets_reps, notes in exercises:
            st.markdown(f"""
<div class="vinyl-card" style="padding:.4rem 1rem;margin:.15rem 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:.85rem">{ex_name}</span>
    <span style="font-family:'Space Mono',monospace;font-size:.75rem;color:#d4681e">{sets_reps}</span>
  </div>
  <div style="font-size:.68rem;color:#9a8878;margin-top:.15rem">{notes}</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    st.markdown("""<div class="vinyl-card vinyl-card-gold" style="font-size:.8rem">
<b>Key Factors:</b> Sleep 8–9h (90% of growth hormone releases during sleep) · Nutrition rich in Zinc, Vitamin D3, Calcium · Consistent daily routine ·
Posture correction compounds over months. Track monthly with a wall measurement at same time of day (morning, before spinal compression sets in).
</div>""", unsafe_allow_html=True)

# ═══════════════════════ PHOTOS ═════════════════════════════════════════════
with tab_photos:
    with st.form("log_photo"):
        pc1,pc2 = st.columns(2)
        with pc1:
            p_date   = st.date_input("Date", value=today)
            p_weight = st.number_input("Body Weight (lbs)", 80.0, 400.0, 170.0, 0.5)
        with pc2:
            p_photo = st.file_uploader("Upload Physique Photo", type=["jpg","jpeg","png","webp"])
            p_notes = st.text_area("Notes (measurements, comments)", height=68)
        if st.form_submit_button("Save Photo Log"):
            filepath = ""
            if p_photo:
                fname = f"physique_{p_date}_{p_photo.name}"
                fpath = PHOTOS_DIR / fname
                img = Image.open(p_photo)
                img.save(str(fpath))
                filepath = str(fpath)
            run_q("INSERT INTO physique_photos (date,filepath,weight_lbs,notes) VALUES (?,?,?,?)",
                  (str(p_date), filepath, p_weight, p_notes.strip()))
            st.success("Photo log saved!"); st.rerun()

    st.markdown("### Photo Log")
    photos = get_q("SELECT date,filepath,weight_lbs,notes FROM physique_photos ORDER BY date DESC LIMIT 30")
    if photos:
        weight_data = [(r[0], r[2]) for r in photos if r[2]]
        if len(weight_data) >= 2:
            weight_data = list(reversed(weight_data))
            fig = go.Figure(go.Scatter(
                x=[w[0] for w in weight_data], y=[w[1] for w in weight_data],
                mode="lines+markers", line=dict(color="#c4a882", width=2),
                marker=dict(size=5, color="#d4681e")))
            fig.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                              font=dict(color="#f0e6d3"), yaxis=dict(title="lbs", gridcolor="#2d2520"),
                              xaxis=dict(color="#9a8878"), margin=dict(l=10,r=10,t=10,b=10), height=200,
                              title=dict(text="Body Weight Over Time", font=dict(color="#c4a882")))
            st.plotly_chart(fig, use_container_width=True)

        cols = st.columns(3)
        for i, p in enumerate(photos):
            with cols[i % 3]:
                st.markdown(f'<div class="label-mono">{p[0]} · {p[2] or "—"}lbs</div>', unsafe_allow_html=True)
                if p[1] and Path(p[1]).exists():
                    try:
                        st.image(p[1], use_column_width=True)
                    except Exception:
                        st.markdown('<span style="color:#9a8878;font-size:.75rem">Image unavailable</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background:#2d2520;height:120px;display:flex;align-items:center;justify-content:center;border-radius:4px;color:#9a8878;font-size:.75rem">No image</div>', unsafe_allow_html=True)
                if p[3]:
                    st.markdown(f'<div style="font-size:.7rem;color:#9a8878">{p[3][:80]}</div>', unsafe_allow_html=True)
    else:
        st.info("No photos logged yet.")

# ═══════════════════════ SUPPLEMENTS ════════════════════════════════════════
with tab_supps:
    st.markdown("### 💊 Daily Supplement Checklist")
    supps = get_q("SELECT id,name,dosage,timing,notes FROM supplements WHERE active=1 ORDER BY timing,name")

    # Group by timing
    timings = {}
    for s in supps:
        timings.setdefault(s[3] or "other", []).append(s)

    timing_order = ["morning","pre-workout","post-workout","evening","other"]
    timing_labels = {"morning":"🌅 Morning","pre-workout":"⚡ Pre-Workout",
                     "post-workout":"🏋️ Post-Workout","evening":"🌙 Evening","other":"📦 Other"}

    if "supp_checks" not in st.session_state:
        st.session_state.supp_checks = {}

    all_taken = True
    for timing in timing_order:
        if timing not in timings: continue
        st.markdown(f'<div class="label-mono" style="margin-top:1rem">{timing_labels.get(timing,timing)}</div>', unsafe_allow_html=True)
        for s in timings[timing]:
            key     = f"supp_{s[0]}"
            checked = st.checkbox(f"**{s[1]}** — {s[2] or ''}", key=key, help=s[4] or "")
            if not checked: all_taken = False
            st.session_state.supp_checks[s[0]] = checked

    if all_taken and supps:
        st.success("✓ All supplements taken for today!")

    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ✏️ Manage Supplements")
    with st.form("add_supp"):
        ac1,ac2,ac3 = st.columns(3)
        with ac1: sn = st.text_input("Supplement Name")
        with ac2: sd = st.text_input("Dosage")
        with ac3: st_val = st.selectbox("Timing", ["morning","pre-workout","post-workout","evening","other"])
        sn_notes = st.text_input("Notes/Reason")
        if st.form_submit_button("Add Supplement"):
            if sn.strip():
                run_q("INSERT INTO supplements (name,dosage,timing,notes) VALUES (?,?,?,?)",
                      (sn.strip(), sd.strip(), st_val, sn_notes.strip()))
                st.rerun()

    all_supps = get_q("SELECT id,name,active FROM supplements")
    for s in all_supps:
        col_a, col_b = st.columns([4,1])
        with col_a:
            status_txt = "active" if s[2] else "inactive"
            st.markdown(f'<div style="font-size:.8rem;color:{"#f0e6d3" if s[2] else "#9a8878"}">{s[1]} — {status_txt}</div>', unsafe_allow_html=True)
        with col_b:
            tog_label = "Deactivate" if s[2] else "Activate"
            if st.button(tog_label, key=f"tog_supp_{s[0]}"):
                run_q("UPDATE supplements SET active=? WHERE id=?", (0 if s[2] else 1, s[0])); st.rerun()

conn.close()
