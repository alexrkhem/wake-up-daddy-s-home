import streamlit as st, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Academics · Jarvis", page_icon="📚", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
from components.rag_engine import load_and_index_pdf, query_textbooks, list_collections, generate_practice_problems
from config import UPLOADS_DIR
import groq # Import the groq library here
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

tab_overview, tab_study, tab_assign, tab_tutor, tab_courses = st.tabs([
    "📊 Overview", "⏱ Study Log", "📝 Assignments", "🧠 AI Tutor", "🎓 Courses"])

# ══════════════════════ OVERVIEW ════════════════════════════════════════════
with tab_overview:
    wk_ago = str(today - datetime.timedelta(days=7))
    mo_ago = str(today - datetime.timedelta(days=30))
    total_wk  = get1("SELECT COALESCE(SUM(duration_mins),0) FROM study_sessions WHERE date>=?",(wk_ago,))[0]
    total_mo  = get1("SELECT COALESCE(SUM(duration_mins),0) FROM study_sessions WHERE date>=?",(mo_ago,))[0]
    open_ass  = get1("SELECT COUNT(*) FROM assignments WHERE status!='done'"                          )[0]
    due_soon  = get1("SELECT COUNT(*) FROM assignments WHERE status!='done' AND due_date<=?",
                     (str(today + datetime.timedelta(days=7)),))[0]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Study Time (7d)",  f"{total_wk//60}h {total_wk%60}m")
    c2.metric("Study Time (30d)", f"{total_mo//60}h {total_mo%60}m")
    c3.metric("Open Assignments", open_ass)
    c4.metric("Due This Week",    due_soon)

    # Time by course
    course_time = get_q("""SELECT c.name, COALESCE(SUM(s.duration_mins),0)
                           FROM courses c LEFT JOIN study_sessions s
                             ON c.id=s.course_id AND s.date>=?
                           WHERE c.active=1 GROUP BY c.id ORDER BY 2 DESC""", (mo_ago,))
    if course_time:
        fig = go.Figure(go.Bar(
            x=[r[0] for r in course_time], y=[r[1] for r in course_time],
            marker_color=[STEM_COLORS.get(r[0],"#d4681e") for r in course_time],
            marker_line_width=0))
        fig.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                          font=dict(color="#f0e6d3", family="Space Mono"),
                          yaxis=dict(title="Minutes", gridcolor="#2d2520"),
                          xaxis=dict(color="#9a8878"),
                          margin=dict(l=10,r=10,t=10,b=10), height=240,
                          title=dict(text="Study Time by Course (30d)", font=dict(color="#c4a882")))
        st.plotly_chart(fig, use_container_width=True)

    # Upcoming due dates
    upcoming = get_q("""SELECT a.title, c.name, a.due_date, a.priority, a.status
                        FROM assignments a JOIN courses c ON a.course_id=c.id
                        WHERE a.status!='done' ORDER BY a.due_date NULLS LAST LIMIT 10""")
    if upcoming:
        st.markdown("### 📅 Upcoming Assignments")
        for a in upcoming:
            days_left = ""
            urgent_color = "#f0e6d3"
            if a[2]:
                d = (datetime.date.fromisoformat(a[2]) - today).days
                urgent_color = "#8b4049" if d <= 2 else "#d4681e" if d <= 7 else "#9a8878"
                days_left = f" · {d}d left" if d >= 0 else " · OVERDUE"
            p_color = {"high":"#e08090","medium":"#d4681e","low":"#7a8c6e"}.get(a[3],"#9a8878")
            course_color = STEM_COLORS.get(a[1], "#9a8878")
            st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{course_color};padding:.4rem 1rem;margin:.2rem 0">
  <div style="display:flex;justify-content:space-between">
    <span style="font-size:.85rem">{a[0]}</span>
    <span style="color:{urgent_color};font-size:.75rem;font-family:'Space Mono',monospace">{a[2] or '—'}{days_left}</span>
  </div>
  <div style="font-size:.65rem;color:#9a8878">{a[1]} · <span style="color:{p_color}">{a[3]}</span></div>
</div>""", unsafe_allow_html=True)

# ══════════════════════ STUDY LOG ═══════════════════════════════════════════
with tab_study:
    with st.form("log_study"):
        sc1,sc2,sc3 = st.columns(3)
        with sc1:
            ss_date   = st.date_input("Date", value=today)
            ss_course = st.selectbox("Course", [""] + [f"{c[1]} ({c[2]})" for c in courses])
        with sc2:
            ss_dur    = st.number_input("Duration (min)", 5, 600, 60, 5)
            ss_prod   = st.slider("Productivity", 1, 5, 3)
        with sc3:
            ss_topic  = st.text_input("Topic / Chapter")
            ss_notes  = st.text_area("Notes", height=68)
        if st.form_submit_button("Log Session"):
            cid = None
            if ss_course:
                for c in courses:
                    if f"{c[1]} ({c[2]})" == ss_course:
                        cid = c[0]; break
            run_q("INSERT INTO study_sessions (date,course_id,duration_mins,topic,notes,productivity) VALUES (?,?,?,?,?,?)",
                  (str(ss_date), cid, ss_dur, ss_topic.strip(), ss_notes.strip(), ss_prod))
            st.success(f"Logged {ss_dur}min!"); st.rerun()

    recent_sessions = get_q("""SELECT s.date,c.name,s.duration_mins,s.topic,s.productivity
                               FROM study_sessions s LEFT JOIN courses c ON s.course_id=c.id
                               ORDER BY s.date DESC, s.id DESC LIMIT 20""")
    prod_colors = {1:"#8b4049",2:"#d4681e",3:"#c4a882",4:"#7a8c6e",5:"#f0e6d3"}
    for s in recent_sessions:
        sdate,cname,sdur,stopic,sprod = s
        cc = STEM_COLORS.get(cname or "", "#9a8878")
        pc = prod_colors.get(sprod, "#9a8878")
        st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{cc};padding:.4rem 1rem;margin:.15rem 0">
  <div style="display:flex;justify-content:space-between">
    <span style="font-size:.82rem">{cname or 'No course'} — {stopic or '—'}</span>
    <span style="font-family:'Space Mono',monospace;font-size:.8rem;color:#d4681e">{sdur}min</span>
  </div>
  <div style="font-size:.65rem;color:#9a8878">{sdate} · Productivity: <span style="color:{pc}">{'■'*(sprod or 1)}{'□'*(5-(sprod or 1))}</span></div>
</div>""", unsafe_allow_html=True)

# ══════════════════════ ASSIGNMENTS ═════════════════════════════════════════
with tab_assign:
    with st.form("add_assignment"):
        ac1,ac2,ac3 = st.columns(3)
        with ac1:
            a_title  = st.text_input("Assignment Title *")
            a_course = st.selectbox("Course", [""] + [f"{c[1]} ({c[2]})" for c in courses])
        with ac2:
            a_due    = st.date_input("Due Date", value=None)
            a_pri    = st.selectbox("Priority", ["high","medium","low"], index=1)
        with ac3:
            a_notes  = st.text_area("Notes", height=68)
        if st.form_submit_button("Add Assignment"):
            if a_title.strip():
                cid = None
                for c in courses:
                    if f"{c[1]} ({c[2]})" == a_course: cid = c[0]; break
                run_q("INSERT INTO assignments (course_id,title,due_date,priority,notes) VALUES (?,?,?,?,?)",
                      (cid, a_title.strip(), str(a_due) if a_due else None, a_pri, a_notes.strip()))
                st.rerun()

    status_filter = st.selectbox("Filter", ["all","todo","in_progress","done"], key="af")
    where = "" if status_filter=="all" else f"WHERE a.status='{status_filter}'"
    assignments = get_q(f"""SELECT a.id,a.title,c.name,a.due_date,a.priority,a.status,a.grade
                            FROM assignments a LEFT JOIN courses c ON a.course_id=c.id
                            {where} ORDER BY a.due_date NULLS LAST""")
    for a in assignments:
        aid,atitle,cname,adue,apri,astatus,agrade = a
        overdue = adue and adue < str(today) and astatus != "done"
        cc  = STEM_COLORS.get(cname or "","#9a8878")
        pc  = {"high":"#e08090","medium":"#d4681e","low":"#7a8c6e"}.get(apri,"#9a8878")
        col_a, col_b, col_c = st.columns([4,1,1])
        with col_a:
            over_tag = ' <span style="font-size:.65rem;color:#8b4049">OVERDUE</span>' if overdue else ""
            done_style = "text-decoration:line-through;opacity:.5;" if astatus=="done" else ""
            grade_html = f' <span style="color:#c4a882">Grade: {agrade}</span>' if agrade else ""
            st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{cc};padding:.4rem 1rem;margin:.15rem 0">
  <span style="font-size:.85rem;{done_style}">{atitle}</span>{over_tag}{grade_html}
  <br><span style="font-size:.65rem;color:#9a8878">{cname or '—'} · <span style="color:{pc}">{apri}</span> · {adue or 'no date'}</span>
</div>""", unsafe_allow_html=True)
        with col_b:
            if astatus != "done":
                if st.button("✓ Done", key=f"adone_{aid}", use_container_width=True):
                    run_q("UPDATE assignments SET status='done' WHERE id=?", (aid,)); st.rerun()
        with col_c:
            if st.button("🗑", key=f"adel_{aid}", use_container_width=True):
                run_q("DELETE FROM assignments WHERE id=?", (aid,)); st.rerun()

# ── RAG TUTOR INTERFACE ──────────────────────────────────────────
    st.markdown("### 🤖 Jarvis AI Textbook Tutor")
    
    # Check for your free Groq Key instead of Anthropic
    if "GROQ_API_KEY" not in st.secrets:
        st.warning("🔗 Free Groq API Key missing. Please add GROQ_API_KEY to your Streamlit Secrets.")
    else:
        # Initialize the free Groq client
        from groq import Groq
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        q_col1, q_col2 = st.columns([2.5, 1.2])
        with q_col1:
            user_q = st.text_input("Ask Jarvis anything about your course textbooks / material:", key="rag_q")
        with q_col2:
            target_course = st.selectbox("Context Course", ["All"] + [c[1] for c in active_courses])

        if user_q.strip():
            with st.spinner("Jarvis is scanning textbook vectors..."):
                # Query your processed textbook vectors
                context_str = query_textbooks(user_q, filter_course=None if target_course=="All" else target_course)
                
                # Construct the prompt for Groq
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

        # ── PRACTICE PROBLEMS GENERATOR ──────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Generate Concept Practice Problems"):
            with st.spinner("Formulating engineering curriculum problems..."):
                try:
                    prob_res = ai_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": f"Generate 3 highly specific engineering practice exam questions (with detailed analytical step-by-step solutions) for these active courses: {[c[1] for c in active_courses]}. Focus heavily on core formulas and structural concepts."}],
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
