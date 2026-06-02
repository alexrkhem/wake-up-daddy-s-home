import streamlit as st, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Academics · Jarvis", page_icon="📚", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
from components.rag_engine import load_and_index_pdf, query_textbooks, list_collections, generate_practice_problems
from config import UPLOADS_DIR
import plotly.graph_objects as go
import tempfile, os
init_db(); apply_styles(); render_jarvis_sidebar()

conn  = get_connection()
today = datetime.date.today()
def run_q(sql,p=()): conn.execute(sql,p); conn.commit()
def get_q(sql,p=()): c=conn.cursor(); c.execute(sql,p); return c.fetchall()
def get1(sql,p=()):  c=conn.cursor(); c.execute(sql,p); r=c.fetchone(); return r

page_header("📚", "Academic Tracker", "courses · study · RAG tutor")

STEM_COLORS = {"Linear Algebra":"#d4681e","Statics":"#c4a882","Chemistry":"#7a8c6e",
               "Calculus":"#8b4049","Physics":"#f0e6d3"}

courses = get_q("SELECT id,name,code,color FROM courses WHERE active=1 ORDER BY name")

# ── TOP KPI ROW ─────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    t_min = get1("SELECT COALESCE(SUM(duration_mins),0) FROM study_sessions")[0]
    st.metric("Total Focus Time", f"{t_min//60}h {t_min%60}m")
with kpi2:
    w_min = get1("SELECT COALESCE(SUM(duration_mins),0) FROM study_sessions WHERE date>=?", (str(today - datetime.timedelta(days=7)),))[0]
    st.metric("Weekly Velocity", f"{w_min//60}h {w_min%60}m")
with kpi3:
    pending = get1("SELECT COUNT(*) FROM assignments WHERE status!='done'")[0]
    st.metric("Pending Assignments", pending)
with kpi4:
    overdue = get1("SELECT COUNT(*) FROM assignments WHERE status!='done' AND due_date<?", (str(today),))[0]
    st.metric("Overdue Tasks", overdue, delta=-overdue if overdue > 0 else 0, delta_color="inverse")

# ── MAIN TABS ───────────────────────────────────────────────────────────────
tab_log, tab_assign, tab_tutor, tab_courses = st.tabs(["⏱ Study Logger", "📝 Assignments", "🧠 AI Tutor", "🗂 Courses"])

# ══════════════════════ STUDY LOGGER ════════════════════════════════════════
with tab_log:
    col_f, col_v = st.columns([1, 1.3])
    with col_f:
        st.markdown("### Log Study Session")
        with st.form("study_form", clear_on_submit=True):
            if not courses:
                st.warning("Add a course in the 'Courses' tab first.")
                s_course = None
            else:
                s_course = st.selectbox("Course", [c[1] for c in courses])
            s_min   = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=60, step=15)
            s_topic = st.text_input("Topic Worked On")
            s_prod  = st.slider("Productivity Rating", 1, 5, 4)
            s_notes = st.text_area("Session Notes / Breakthroughs", height=70)
            if st.form_submit_button("Log Session") and s_course:
                c_id = next(c[0] for c in courses if c[1] == s_course)
                run_q("INSERT INTO study_sessions (date,course_id,duration_mins,topic,notes,productivity) VALUES (?,?,?,?,?,?)",
                      (str(today), c_id, s_min, s_topic.strip(), s_notes.strip(), s_prod))
                st.success("Session logged.")
                st.rerun()

    with col_v:
        st.markdown("### Focus Allocation")
        alloc = get_q("""SELECT c.name, SUM(s.duration_mins) 
                         FROM study_sessions s JOIN courses c ON s.course_id=c.id 
                         GROUP BY c.name""")
        if alloc:
            labels = [a[0] for a in alloc]
            values = [a[1] for a in alloc]
            colors = [STEM_COLORS.get(l, "#9a8878") for l in labels]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6,
                                         marker=dict(colors=colors),
                                         textinfo='label+percent',
                                         hoverinfo='value',
                                         textfont=dict(color="#f0e6d3", size=10))])
            fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=230,
                              showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown('<div style="color:#9a8878;padding:2rem 0;text-align:center;font-size:.8rem">No tracking data gathered yet.</div>', unsafe_allow_html=True)

    st.markdown("### Recent Deep Work Log")
    recent_s = get_q("""SELECT s.date, c.name, s.duration_mins, s.topic, s.productivity, c.color 
                        FROM study_sessions s JOIN courses c ON s.course_id=c.id 
                        ORDER BY s.date DESC, s.id DESC LIMIT 5""")
    for rs in recent_s:
        st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{rs[5] or '#d4681e'};padding:.45rem .8rem;margin:.15rem 0">
  <span style="font-size:.8rem;color:#f0e6d3;font-weight:bold">{rs[1]}</span>
  <span style="font-size:.7rem;color:#9a8878;margin-left:.5rem">{rs[0]} · {rs[2]} mins · Prod: {rs[4]}/5</span>
  <br><span style="font-size:.72rem;color:#c4a882">{rs[3] or 'General Review'}</span>
</div>""", unsafe_allow_html=True)

# ══════════════════════ ASSIGNMENTS ════════════════════════════════════════
with tab_assign:
    col_as1, col_as2 = st.columns([1, 1.2])
    with col_as1:
        st.markdown("### New Deliverable")
        with st.form("assign_form", clear_on_submit=True):
            if not courses: st.warning("Add a course first."); a_course = None
            else: a_course = st.selectbox("Course Context", [c[1] for c in courses])
            a_title = st.text_input("Assignment Title *")
            a_due   = st.date_input("Due Date", today + datetime.timedelta(days=2))
            a_prio  = st.select_slider("Priority Allocation", ["low", "medium", "high"], value="medium")
            a_notes = st.text_area("Requirements / References", height=60)
            if st.form_submit_button("Queue Assignment") and a_title.strip() and a_course:
                c_id = next(c[0] for c in courses if c[1] == a_course)
                run_q("INSERT INTO assignments (course_id,title,due_date,priority,status,notes) VALUES (?,?,?,?,'todo',?)",
                      (c_id, a_title.strip(), str(a_due), a_prio, a_notes.strip()))
                st.success("Task queued.")
                st.rerun()

    with col_as2:
        st.markdown("### Pipeline Matrix")
        tasks = get_q("""SELECT a.id, a.title, a.due_date, a.priority, a.status, c.name, c.color 
                         FROM assignments a JOIN courses c ON a.course_id=c.id 
                         WHERE a.status!='done' ORDER BY a.due_date ASC""")
        if tasks:
            for t in tasks:
                tid, ttitle, tdue, tprio, tstat, tcname, tccol = t
                p_color = {"high":"#d4681e","medium":"#c4a882","low":"#7a8c6e"}.get(tprio, "#9a8878")
                st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{tccol or '#d4681e'};padding:.5rem .8rem;margin:.25rem 0">
  <div style="display:flex;justify-content:between;align-items:center">
    <span style="font-size:.82rem;font-weight:bold;color:#f0e6d3">{ttitle}</span>
    <span style="font-size:.62rem;text-transform:uppercase;color:{p_color};border:1px solid {p_color};padding:1px 4px;border-radius:2px;margin-left:auto">{tprio}</span>
  </div>
  <span style="font-size:.68rem;color:#9a8878">{tcname} · Due: {tdue}</span>
</div>""", unsafe_allow_html=True)
                if st.button("Mark Complete", key=f"tcomp_{tid}"):
                    run_q("UPDATE assignments SET status='done' WHERE id=?", (tid,))
                    st.rerun()
        else:
            st.markdown('<div style="color:#9a8878;padding:2rem 0;text-align:center;font-size:.8rem">Clear horizon. All items completed.</div>', unsafe_allow_html=True)

# ══════════════════════ AI TUTOR ════════════════════════════════════════════
with tab_tutor:
    st.markdown("### 🤖 Jarvis AI Textbook Tutor")
    
    if "GROQ_API_KEY" not in st.secrets:
        st.warning("🔗 Free Groq API Key missing. Please add GROQ_API_KEY to your Streamlit Secrets.")
    else:
        from groq import Groq
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        q_col1, q_col2 = st.columns([2.5, 1.2])
        with q_col1:
            user_q = st.text_input("Ask Jarvis anything about your course textbooks / material:", key="rag_q")
        with q_col2:
            target_course = st.selectbox("Context Course", ["All"] + [c[1] for c in courses])

        if user_q.strip():
            with st.spinner("Jarvis is scanning textbook vectors..."):
                context_str = query_textbooks(user_q, filter_course=None if target_course=="All" else target_course)
                
                messages = [
                    {"role": "system", "content": f"You are Jarvis, an elite engineering tutor. Answer the user's question accurately using this textbook context:\n\n{context_str}\n\nProvide deep architectural and clear mathematical breakdowns."},
                    {"role": "user", "content": user_q}
                ]
                
                try:
                    res = ai_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        max_tokens=2048
                    )
                    st.markdown(f"""<div style="background:#23201c;border-left:3px solid #c4a882;padding:1rem;border-radius:4px;margin-top:1rem">
                    <span style="color:#f0e6d3;font-size:.9rem">{res.choices[0].message.content}</span></div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Tutor Run Error: {e}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Generate Concept Practice Problems"):
            with st.spinner("Formulating engineering curriculum problems..."):
                try:
                    prob_res = ai_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": f"Generate 3 highly specific engineering practice exam questions (with detailed analytical step-by-step solutions) for these active courses: {[c[1] for c in courses]}. Focus heavily on core formulas and structural concepts."}],
                        max_tokens=2048
                    )
                    st.markdown(f"""<div style="background:#1d1b18;border:1px dashed #3d3028;padding:1rem;border-radius:4px">
                    <span style="color:#f0e6d3;font-size:.88rem;white-space:pre-wrap">{prob_res.choices[0].message.content}</span></div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Problem Generator Error: {e}")

# ══════════════════════ COURSES ═════════════════════════════════════════════
with tab_courses:
    st.markdown("### Manage Courses")
    with st.form("add_course"):
        cc1,cc2,cc3 = st.columns(3)
        with cc1: cname    = st.text_input("Course Name *")
        with cc2: ccode    = st.text_input("Code (e.g. MATH-2310)")
        with cc3: csemester= st.text_input("Semester (e.g. Fall 2025)")
        ccolor   = st.color_picker("Color", "#d4681e")
        if st.form_submit_button("Add Course"):
            if cname.strip():
                run_q("INSERT INTO courses (name,code,semester,color) VALUES (?,?,?,?)",
                      (cname.strip(), ccode.strip(), csemester.strip(), ccolor))
                st.rerun()

    all_courses = get_q("SELECT id,name,code,semester,color,active FROM courses ORDER BY active DESC,name")
    for c in all_courses:
        cid,cname,ccode,csem,ccol,cactive = c
        col_a, col_b = st.columns([5,1])
        with col_a:
            study_total = get1("SELECT COALESCE(SUM(duration_mins),0) FROM study_sessions WHERE course_id=?", (cid,))[0]
            st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{ccol or '#d4681e'};padding:.4rem 1rem;margin:.2rem 0;{'opacity:.4;' if not cactive else ''}">
  <span style="font-size:.88rem">{cname}</span>
  <span style="font-size:.7rem;color:#9a8878;margin-left:.5rem">{ccode or ''} · {csem or ''}</span>
  <br><span style="font-size:.65rem;color:#9a8878">{study_total//60}h {study_total%60}m total study time</span>
</div>""", unsafe_allow_html=True)
        with col_b:
            if st.button("Archive" if cactive else "Restore", key=f"ctog_{cid}"):
                run_q("UPDATE courses SET active=? WHERE id=?", (0 if cactive else 1, cid)); st.rerun()

conn.close()