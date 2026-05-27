import streamlit as st, sys, datetime, shutil, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Design Projects · Jarvis", page_icon="🎨", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
from config import FILES_DIR
import plotly.graph_objects as go
init_db(); apply_styles(); render_jarvis_sidebar()

conn  = get_connection()
today = datetime.date.today()
def run_q(sql,p=()): conn.execute(sql,p); conn.commit()
def get_q(sql,p=()): c=conn.cursor(); c.execute(sql,p); return c.fetchall()
def get1(sql,p=()):  c=conn.cursor(); c.execute(sql,p); r=c.fetchone(); return r

FILE_TYPES = {"cad":"🔧","word":"📄","image":"🖼","ppt":"📊","pdf":"📑","other":"📁"}
STATUS_COLORS = {"active":"#7a8c6e","on_hold":"#d4681e","completed":"#c4a882"}

page_header("🎨", "Design Project Tracker", "EDP · files · milestones")

st.markdown(f'<div class="label-mono">Permanent file storage: <span style="color:#d4681e">{FILES_DIR}</span></div>', unsafe_allow_html=True)

tab_projects, tab_files, tab_edp = st.tabs(["🗂 Projects", "📂 File Manager", "📐 EDP Planner"])

# ══════════════════════ PROJECTS ════════════════════════════════════════════
with tab_projects:
    with st.expander("＋ New Project"):
        with st.form("new_project"):
            pc1,pc2 = st.columns(2)
            with pc1:
                p_name  = st.text_input("Project Name *")
                p_start = st.date_input("Start Date", value=today)
                p_tags  = st.text_input("Tags (comma-separated)")
            with pc2:
                p_status  = st.selectbox("Status", ["active","on_hold","completed"])
                p_deadline= st.date_input("Deadline", value=None)
                p_website = st.checkbox("Website-ready portfolio piece?")
            p_desc = st.text_area("Description", height=80)
            if st.form_submit_button("Create Project"):
                if p_name.strip():
                    run_q("INSERT INTO design_projects (name,description,status,start_date,deadline,tags,website_ready) VALUES (?,?,?,?,?,?,?)",
                          (p_name.strip(), p_desc.strip(), p_status,
                           str(p_start), str(p_deadline) if p_deadline else None,
                           p_tags.strip(), int(p_website)))
                    proj_id = get1("SELECT last_insert_rowid()")[0]
                    proj_dir = FILES_DIR / p_name.strip().replace(" ","_")
                    proj_dir.mkdir(exist_ok=True)
                    st.success(f"Project created! Files will be stored in {proj_dir}"); st.rerun()

    status_f = st.selectbox("Filter", ["all","active","on_hold","completed"], key="pf")
    where = "" if status_f=="all" else f"WHERE status='{status_f}'"
    projects = get_q(f"SELECT id,name,description,status,start_date,deadline,tags,website_ready FROM design_projects {where} ORDER BY status,deadline NULLS LAST")

    for p in projects:
        pid,pname,pdesc,pstatus,pstart,pdeadline,ptags,pwebsite = p
        sc    = STATUS_COLORS.get(pstatus,"#9a8878")
        files_count = get1("SELECT COUNT(*) FROM project_files WHERE project_id=?",(pid,))[0]
        ms_count    = get1("SELECT COUNT(*) FROM project_milestones WHERE project_id=?",(pid,))[0]
        ms_done     = get1("SELECT COUNT(*) FROM project_milestones WHERE project_id=? AND status='done'",(pid,))[0]
        days_left = ""
        if pdeadline:
            d = (datetime.date.fromisoformat(pdeadline) - today).days
            urgency = "#8b4049" if d <= 7 else "#d4681e" if d <= 30 else "#9a8878"
            days_left = f' <span style="color:{urgency}">{d}d left</span>'

        with st.expander(f"{'🌐' if pwebsite else ''} {pname}  [{pstatus.replace('_',' ')}] — {files_count} files · {ms_done}/{ms_count} milestones"):
            col_info, col_actions = st.columns([3,1])
            with col_info:
                st.markdown(f'<div style="font-size:.8rem;color:#9a8878">{pdesc or ""}</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="font-size:.72rem;color:#9a8878;margin-top:.3rem">Started: {pstart} &nbsp;·&nbsp; Deadline: {pdeadline or "—"}{days_left}</div>', unsafe_allow_html=True)
                if ptags:
                    tags_html = " ".join(f'<span class="badge badge-medium">{t.strip()}</span>' for t in ptags.split(",") if t.strip())
                    st.markdown(tags_html, unsafe_allow_html=True)

            with col_actions:
                new_status = {"active":"on_hold","on_hold":"completed","completed":"active"}
                if st.button(f"→ {new_status[pstatus].replace('_',' ').title()}", key=f"pstatus_{pid}"):
                    run_q("UPDATE design_projects SET status=? WHERE id=?", (new_status[pstatus], pid)); st.rerun()
                if st.button("🗑 Delete", key=f"pdel_{pid}"):
                    run_q("DELETE FROM design_projects WHERE id=?", (pid,)); st.rerun()

            # Milestones
            st.markdown('<div style="font-size:.8rem;font-weight:700;margin-top:.5rem;color:#c4a882">Milestones</div>', unsafe_allow_html=True)
            milestones = get_q("SELECT id,title,due_date,status,notes FROM project_milestones WHERE project_id=? ORDER BY due_date",(pid,))
            for ms in milestones:
                msid,mstitle,msdue,msstatus,msnotes = ms
                mc = "#7a8c6e" if msstatus=="done" else "#d4681e"
                done_s = "text-decoration:line-through;opacity:.5;" if msstatus=="done" else ""
                col_ms,col_msbtn = st.columns([5,1])
                with col_ms:
                    st.markdown(f'<div style="font-size:.78rem;{done_s}color:#f0e6d3;padding:.2rem 0"><span style="color:{mc}">{"✓" if msstatus=="done" else "○"}</span> {mstitle} <span style="color:#9a8878">({msdue or "—"})</span></div>', unsafe_allow_html=True)
                with col_msbtn:
                    if st.button("✓" if msstatus!="done" else "↺", key=f"mstog_{msid}"):
                        run_q("UPDATE project_milestones SET status=? WHERE id=?",
                              ("done" if msstatus!="done" else "pending", msid)); st.rerun()

            with st.form(f"add_ms_{pid}"):
                mc1,mc2 = st.columns(2)
                with mc1: ms_title = st.text_input("Milestone", key=f"mst_{pid}")
                with mc2: ms_due   = st.date_input("Due", value=None, key=f"msd_{pid}")
                if st.form_submit_button("Add Milestone"):
                    if ms_title.strip():
                        run_q("INSERT INTO project_milestones (project_id,title,due_date) VALUES (?,?,?)",
                              (pid, ms_title.strip(), str(ms_due) if ms_due else None))
                        st.rerun()

# ══════════════════════ FILE MANAGER ════════════════════════════════════════
with tab_files:
    st.markdown("### 📂 Project File Manager")
    st.markdown(f'<div style="font-size:.78rem;color:#9a8878;margin-bottom:.5rem">Files are saved permanently to <code>{FILES_DIR}</code> on your hard drive and will persist across app restarts.</div>', unsafe_allow_html=True)

    projects_list = get_q("SELECT id,name FROM design_projects ORDER BY name")
    if not projects_list:
        st.info("Create a project first.")
    else:
        sel_project_name = st.selectbox("Select Project", [p[1] for p in projects_list])
        sel_pid = next((p[0] for p in projects_list if p[1] == sel_project_name), None)

        if sel_pid:
            proj_dir = FILES_DIR / sel_project_name.replace(" ","_")
            proj_dir.mkdir(exist_ok=True)

            # Upload
            with st.form("upload_file"):
                uf1,uf2 = st.columns(2)
                with uf1:
                    uploaded = st.file_uploader("Upload File",
                        type=["pdf","docx","doc","dwg","dxf","png","jpg","jpeg","pptx","ppt","xlsx","stl","stp","step","igs","heic"])
                    file_type = st.selectbox("File Type", ["cad","word","image","ppt","pdf","other"])
                with uf2:
                    file_notes = st.text_area("Notes / Description", height=80)
                if st.form_submit_button("💾 Save to Dashboard"):
                    if uploaded:
                        dest = proj_dir / uploaded.name
                        with open(str(dest), "wb") as f:
                            f.write(uploaded.getvalue())
                        run_q("INSERT INTO project_files (project_id,filename,filepath,file_type,notes) VALUES (?,?,?,?,?)",
                              (sel_pid, uploaded.name, str(dest), file_type, file_notes.strip()))
                        st.success(f"Saved '{uploaded.name}' to {dest}"); st.rerun()
                    else:
                        st.error("No file selected.")

            # File browser
            st.markdown("### Saved Files")
            project_files = get_q("SELECT id,filename,filepath,file_type,notes,uploaded_at FROM project_files WHERE project_id=? ORDER BY uploaded_at DESC", (sel_pid,))

            if project_files:
                type_filter = st.selectbox("Filter by type", ["all"] + list(FILE_TYPES.keys()), key="ff")
                for pf in project_files:
                    fid,fname,fpath,ftype,fnotes,fuploaded = pf
                    if type_filter != "all" and ftype != type_filter: continue
                    ficon = FILE_TYPES.get(ftype,"📁")
                    exists = Path(fpath).exists() if fpath else False
                    exist_color = "#7a8c6e" if exists else "#8b4049"
                    exist_txt   = "✓ on disk" if exists else "⚠ file not found"

                    col_f, col_fb = st.columns([5,1])
                    with col_f:
                        st.markdown(f"""
<div class="vinyl-card" style="padding:.4rem 1rem;margin:.2rem 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:.85rem">{ficon} {fname}</span>
    <span style="font-size:.65rem;color:{exist_color}">{exist_txt}</span>
  </div>
  <div style="font-size:.65rem;color:#9a8878">{ftype} · {fuploaded[:16]} · {fnotes or ''}</div>
  <div style="font-size:.62rem;color:#3d3028;margin-top:.2rem">{fpath}</div>
</div>""", unsafe_allow_html=True)

                        # Preview images
                        if ftype == "image" and exists:
                            try:
                                st.image(fpath, width=200)
                            except Exception:
                                pass

                    with col_fb:
                        if st.button("🗑", key=f"fdel_{fid}"):
                            run_q("DELETE FROM project_files WHERE id=?", (fid,)); st.rerun()
            else:
                st.info("No files uploaded for this project yet.")

            # Show disk folder contents
            with st.expander("📁 View Disk Folder"):
                disk_files = sorted(proj_dir.iterdir()) if proj_dir.exists() else []
                if disk_files:
                    for df in disk_files:
                        size = df.stat().st_size / 1024
                        st.markdown(f'<div style="font-size:.75rem;color:#9a8878;padding:.1rem 0">📄 {df.name} — {size:.1f} KB</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<span style="font-size:.75rem;color:#9a8878">Folder is empty.</span>', unsafe_allow_html=True)

# ══════════════════════ EDP PLANNER ═════════════════════════════════════════
with tab_edp:
    st.markdown("### 📐 Engineering Design Process Planner")
    projects_list2 = get_q("SELECT id,name FROM design_projects WHERE status='active' ORDER BY name")
    if not projects_list2:
        st.info("No active projects. Create one in the Projects tab.")
    else:
        edp_proj = st.selectbox("Select Active Project", [p[1] for p in projects_list2], key="edp_proj")
        edp_pid  = next((p[0] for p in projects_list2 if p[1] == edp_proj), None)

        EDP_PHASES = [
            ("1. Define the Problem",          "Problem statement, stakeholder needs, functional requirements"),
            ("2. Research & Background",        "Literature review, existing solutions, constraints, standards"),
            ("3. Brainstorm Concepts",          "Concept sketches, morphological chart, design alternatives"),
            ("4. Select Best Concept",          "Decision matrix / Pugh chart, concept down-selection"),
            ("5. Develop & Detail",             "CAD models, calculations, material selection, tolerances"),
            ("6. Prototype & Test",             "Build prototype, test against requirements, collect data"),
            ("7. Evaluate & Iterate",           "Compare results to requirements, identify improvements"),
            ("8. Final Design & Documentation", "Final drawings, BOM, assembly instructions, report"),
        ]

        if edp_pid:
            milestones_edp = get_q("SELECT title,due_date,status FROM project_milestones WHERE project_id=? ORDER BY due_date", (edp_pid,))
            ms_by_title    = {m[0]: m for m in milestones_edp}

            for phase_title, phase_desc in EDP_PHASES:
                ms   = ms_by_title.get(phase_title)
                status_edp = ms[2] if ms else "pending"
                due_edp    = ms[1] if ms else None
                phase_color = "#7a8c6e" if status_edp=="done" else "#d4681e" if due_edp and due_edp < str(today) else "#9a8878"
                done_style  = "text-decoration:line-through;opacity:.5;" if status_edp=="done" else ""

                col_ph, col_set = st.columns([4,1])
                with col_ph:
                    st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{phase_color};padding:.5rem 1rem;margin:.2rem 0">
  <div style="font-size:.85rem;{done_style}color:#f0e6d3">{phase_title}</div>
  <div style="font-size:.68rem;color:#9a8878">{phase_desc}</div>
  {f'<div style="font-size:.65rem;color:{phase_color}">Due: {due_edp}</div>' if due_edp else ''}
</div>""", unsafe_allow_html=True)
                with col_set:
                    if not ms:
                        new_due = st.date_input("Set due", value=None, key=f"edpdue_{phase_title[:15]}")
                        if st.button("Set", key=f"edpadd_{phase_title[:15]}"):
                            run_q("INSERT INTO project_milestones (project_id,title,due_date) VALUES (?,?,?)",
                                  (edp_pid, phase_title, str(new_due) if new_due else None))
                            st.rerun()
                    else:
                        tog_label = "✓ Done" if status_edp!="done" else "↺ Reopen"
                        if st.button(tog_label, key=f"edptog_{phase_title[:15]}"):
                            ms_id = get1("SELECT id FROM project_milestones WHERE project_id=? AND title=?", (edp_pid, phase_title))
                            if ms_id:
                                run_q("UPDATE project_milestones SET status=? WHERE id=?",
                                      ("done" if status_edp!="done" else "pending", ms_id[0]))
                                st.rerun()

            # Timeline chart
            ms_data = get_q("SELECT title,due_date,status FROM project_milestones WHERE project_id=? AND due_date IS NOT NULL ORDER BY due_date", (edp_pid,))
            if ms_data:
                st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
                fig = go.Figure()
                colors = {"done":"#7a8c6e","pending":"#d4681e"}
                for i, (mtitle, mdue, mstatus) in enumerate(ms_data):
                    fig.add_trace(go.Scatter(
                        x=[mdue], y=[i],
                        mode="markers+text",
                        marker=dict(size=12, color=colors.get(mstatus,"#9a8878"),
                                    symbol="diamond"),
                        text=[mtitle[:25]+"…" if len(mtitle)>25 else mtitle],
                        textposition="middle right",
                        textfont=dict(color="#f0e6d3", size=10),
                        showlegend=False
                    ))
                fig.add_vline(x=str(today), line_dash="dash", line_color="#c4a882",
                              annotation_text="Today", annotation_font_color="#c4a882")
                fig.update_layout(
                    paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                    font=dict(color="#f0e6d3", family="Space Mono"),
                    yaxis=dict(visible=False), xaxis=dict(color="#9a8878", gridcolor="#2d2520"),
                    margin=dict(l=10,r=180,t=20,b=10), height=max(180, len(ms_data)*35),
                    title=dict(text="Project Timeline", font=dict(color="#c4a882"))
                )
                st.plotly_chart(fig, use_container_width=True)

conn.close()
