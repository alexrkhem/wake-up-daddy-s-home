import streamlit as st, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Academics · Jarvis", page_icon="📚", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
from components.rag_engine import load_and_index_pdf, query_textbooks, list_collections, generate_practice_problems
from config import UPLOADS_DIR, ANTHROPIC_API_KEY
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

# ══════════════════════ AI TUTOR (RAG) ══════════════════════════════════════
with tab_tutor:
    st.markdown("### 🧠 Jarvis AI Tutor")

    if not ANTHROPIC_API_KEY:
        st.warning("Set ANTHROPIC_API_KEY in .env to use the AI tutor.")
    else:
        col_upload, col_query = st.columns([1, 1.5])

        with col_upload:
            st.markdown("#### 📖 Upload Textbooks")
            st.markdown('<div style="font-size:.78rem;color:#9a8878;margin-bottom:.5rem">Upload PDF textbooks. Jarvis will index them and use them to answer your questions and generate practice problems.</div>', unsafe_allow_html=True)
            pdf_file = st.file_uploader("Upload PDF Textbook", type=["pdf"])
            tb_course = st.selectbox("Link to Course", ["None"] + [c[1] for c in courses])
            tb_title  = st.text_input("Textbook Title (e.g. 'Stewart Calculus 8e')")

            if st.button("📥 Index Textbook") and pdf_file and tb_title.strip():
                with st.spinner("Indexing textbook… this may take a minute for large PDFs"):
                    fpath = UPLOADS_DIR / f"tb_{pdf_file.name}"
                    with open(str(fpath), "wb") as f:
                        f.write(pdf_file.getvalue())
                    coll_name = tb_title.strip().lower().replace(" ", "_")[:30]
                    success = load_and_index_pdf(str(fpath), coll_name)
                    if success:
                        cid = None
                        for c in courses:
                            if c[1] == tb_course: cid = c[0]; break
                        run_q("INSERT INTO textbooks (course_id,title,filepath,vectorized) VALUES (?,?,?,1)",
                              (cid, tb_title.strip(), str(fpath)))
                        st.success(f"'{tb_title}' indexed! Jarvis can now query it.")
                    else:
                        st.error("Indexing failed. Check requirements (pypdf, chromadb, langchain-community).")

            st.markdown("**Indexed Textbooks:**")
            indexed = get_q("SELECT t.title,c.name FROM textbooks t LEFT JOIN courses c ON t.course_id=c.id WHERE t.vectorized=1")
            if indexed:
                for tb in indexed:
                    st.markdown(f'<div style="font-size:.78rem;color:#7a8c6e">✓ {tb[0]} ({tb[1] or "no course"})</div>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="font-size:.75rem;color:#9a8878">No textbooks indexed yet.</span>', unsafe_allow_html=True)

        with col_query:
            st.markdown("#### 💬 Ask Jarvis / Generate Problems")
            collections = list_collections()
            sel_coll = st.selectbox("Textbook to query (optional)", ["None — general knowledge"] + collections)
            query_type = st.radio("Mode", ["Ask a question","Generate practice problems"], horizontal=True)
            question = st.text_area("Question / Topic", height=90,
                                    placeholder="e.g. 'Explain Gaussian elimination' or 'Statics equilibrium — 3D forces'")
            course_context = st.selectbox("Course context", ["General"] + [c[1] for c in courses])

            if st.button("🎓 Ask Jarvis", type="primary"):
                if question.strip():
                    with st.spinner("Jarvis is thinking…"):
                        context = ""
                        if sel_coll and sel_coll != "None — general knowledge":
                            context = query_textbooks(question, sel_coll)

                        if query_type == "Generate practice problems":
                            result = generate_practice_problems(question.strip(), course_context, context)
                        else:
                            if not ANTHROPIC_API_KEY:
                                result = "Set ANTHROPIC_API_KEY to use tutor."
                            else:
                                import anthropic
                                client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                                sys_prompt = f"""You are a brilliant STEM tutor specializing in {course_context}.
Answer the student's question clearly and thoroughly.
Use step-by-step explanations. Use LaTeX notation ($...$) for math.
If textbook context is provided, reference it and cite page numbers where relevant."""
                                if context:
                                    sys_prompt += f"\n\nTextbook context:\n{context[:3000]}"
                                resp = client.messages.create(
                                    model="claude-sonnet-4-20250514", max_tokens=1500,
                                    messages=[{"role":"user","content":question.strip()}],
                                    system=sys_prompt)
                                result = resp.content[0].text

                        st.session_state["tutor_result"] = result
                else:
                    st.error("Enter a question or topic.")

            if "tutor_result" in st.session_state:
                st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
                st.markdown(st.session_state["tutor_result"])

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
