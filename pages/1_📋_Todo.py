import streamlit as st, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Todo · Jarvis", page_icon="📋", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
init_db(); apply_styles(); render_jarvis_sidebar()

conn  = get_connection()
today = datetime.date.today()

def run_q(sql, p=()):
    conn.execute(sql, p); conn.commit()
def get_q(sql, p=()):
    c=conn.cursor(); c.execute(sql,p); return c.fetchall()

page_header("📋", "Todo List", "task tracker")

# ── Add Todo ────────────────────────────────────────────────────────────────
with st.expander("＋  Add New Todo", expanded=False):
    with st.form("add_todo"):
        c1,c2,c3 = st.columns([2,1,1])
        with c1: title = st.text_input("Title *")
        with c2: priority = st.selectbox("Priority", ["high","medium","low"], index=1)
        with c3: target_date = st.date_input("Target Date", value=None)
        desc = st.text_area("Description", height=60)
        if st.form_submit_button("Add Todo"):
            if title.strip():
                run_q("INSERT INTO todos (title,description,target_date,priority) VALUES (?,?,?,?)",
                      (title.strip(), desc.strip(), str(target_date) if target_date else None, priority))
                st.success("Added!"); st.rerun()
            else:
                st.error("Title required.")

# ── Filters ─────────────────────────────────────────────────────────────────
fc1,fc2,fc3 = st.columns([1,1,2])
with fc1: status_f  = st.selectbox("Status",["all","todo","in_progress","done"])
with fc2: priority_f= st.selectbox("Priority",["all","high","medium","low"])
with fc3: search_f  = st.text_input("Search", placeholder="Search todos…")

conds = []; params = []
if status_f   != "all": conds.append("status=?");   params.append(status_f)
if priority_f != "all": conds.append("priority=?"); params.append(priority_f)
if search_f:            conds.append("title LIKE ?"); params.append(f"%{search_f}%")
where = ("WHERE " + " AND ".join(conds)) if conds else ""

todos = get_q(f"""SELECT id,title,description,target_date,priority,status,created_at
               FROM todos {where}
               ORDER BY CASE status WHEN 'todo' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END,
                        CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                        target_date NULLS LAST""", params)

# ── Stats ────────────────────────────────────────────────────────────────────
all_todos = get_q("SELECT status, COUNT(*) FROM todos GROUP BY status")
stats = {r[0]:r[1] for r in all_todos}
s1,s2,s3,s4 = st.columns(4)
s1.metric("Todo",       stats.get("todo",0))
s2.metric("In Progress",stats.get("in_progress",0))
s3.metric("Done",       stats.get("done",0))
overdue_n = len([t for t in todos if t[3] and t[3]<str(today) and t[5]!="done"])
s4.metric("Overdue",    overdue_n)

st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)

# ── Todo Cards ───────────────────────────────────────────────────────────────
if not todos:
    st.info("No todos match your filter.")
else:
    for t in todos:
        tid, title, desc, tdate, pri, status, created = t
        overdue = tdate and tdate < str(today) and status != "done"
        p_colors = {"high":"#e08090","medium":"#d4681e","low":"#7a8c6e"}
        s_colors = {"todo":"#9a8878","in_progress":"#d4681e","done":"#7a8c6e"}
        border   = p_colors.get(pri, "#9a8878")
        op       = 0.4 if status == "done" else 1.0

        with st.container():
            ca, cb = st.columns([5, 1])
            with ca:
                over_tag = ' <span style="font-size:.65rem;color:#8b4049;font-weight:700">● OVERDUE</span>' if overdue else ""
                done_style = "text-decoration:line-through;opacity:.5;" if status=="done" else ""
                st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{border};opacity:{op}">
  <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap">
    <span style="font-size:.95rem;{done_style}">{title}</span>
    <span class="badge badge-{pri}">{pri}</span>
    <span class="badge badge-{'done' if status=='done' else 'inprog' if status=='in_progress' else 'todo'}">{status.replace('_',' ')}</span>
    {over_tag}
  </div>
  {f'<div style="font-size:.75rem;color:#9a8878;margin-top:.25rem">{desc}</div>' if desc else ''}
  <div style="font-size:.65rem;color:#9a8878;margin-top:.3rem">
    {'📅 ' + tdate if tdate else 'No date'} &nbsp;·&nbsp; Created {created[:10]}
  </div>
</div>""", unsafe_allow_html=True)

            with cb:
                st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
                next_status = {"todo":"in_progress","in_progress":"done","done":"todo"}
                next_label  = {"todo":"▶ Start","in_progress":"✓ Done","done":"↺ Reopen"}
                if st.button(next_label.get(status,"→"), key=f"ns_{tid}", use_container_width=True):
                    run_q("UPDATE todos SET status=? WHERE id=?", (next_status[status], tid))
                    st.rerun()
                if st.button("🗑", key=f"del_{tid}", use_container_width=True):
                    run_q("DELETE FROM todos WHERE id=?", (tid,))
                    st.rerun()

conn.close()
