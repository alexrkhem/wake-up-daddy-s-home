import streamlit as st, sys, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Journal · Jarvis", page_icon="📓", layout="wide")
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

WIN_CATS = ["fitness","academic","music","finance","personal","creative","work","social","health"]
MOOD_LABELS = {1:"😞 Rough",2:"😕 Low",3:"😐 Okay",4:"🙂 Good",5:"😊 Solid",
               6:"😌 Calm",7:"😄 Great",8:"🤩 Excellent",9:"🔥 On fire",10:"💫 Peak"}

page_header("📓", "Journal & Win Log", "reflect · log · grow")

# ── Win Streak ───────────────────────────────────────────────────────────────
streak = 0
for i in range(365):
    d = str(today - datetime.timedelta(days=i))
    if get1("SELECT COUNT(*) FROM wins WHERE date=?", (d,))[0]:
        streak += 1
    elif i > 0:
        break

total_wins   = get1("SELECT COUNT(*) FROM wins")[0]
total_entries= get1("SELECT COUNT(*) FROM journal_entries")[0]
total_lessons= get1("SELECT COUNT(*) FROM lessons_learned")[0]
wins_month   = get1("SELECT COUNT(*) FROM wins WHERE date>=?", (str(today.replace(day=1)),))[0]

# Hero streak display
st.markdown(f"""
<div style="background:#2d2520;border:1px solid #c4a882;border-radius:6px;
padding:1.5rem;text-align:center;margin-bottom:1.5rem;
background:linear-gradient(135deg,#23201c 0%,#2d2520 100%)">
  <div style="font-family:'Playfair Display',serif;font-size:4rem;color:#c4a882;line-height:1">{streak}</div>
  <div style="font-size:.7rem;color:#9a8878;letter-spacing:3px;text-transform:uppercase;margin-top:.3rem">Day Win Streak</div>
  <div style="height:1px;background:linear-gradient(to right,transparent,#c4a882,transparent);margin:1rem auto;width:60%"></div>
  <div style="display:flex;justify-content:center;gap:3rem">
    <div><div style="font-family:'Space Mono',monospace;font-size:1.4rem;color:#d4681e">{total_wins}</div>
         <div style="font-size:.62rem;color:#9a8878;text-transform:uppercase;letter-spacing:1px">All-Time Wins</div></div>
    <div><div style="font-family:'Space Mono',monospace;font-size:1.4rem;color:#7a8c6e">{wins_month}</div>
         <div style="font-size:.62rem;color:#9a8878;text-transform:uppercase;letter-spacing:1px">This Month</div></div>
    <div><div style="font-family:'Space Mono',monospace;font-size:1.4rem;color:#c4a882">{total_entries}</div>
         <div style="font-size:.62rem;color:#9a8878;text-transform:uppercase;letter-spacing:1px">Journal Entries</div></div>
    <div><div style="font-family:'Space Mono',monospace;font-size:1.4rem;color:#f0e6d3">{total_lessons}</div>
         <div style="font-size:.62rem;color:#9a8878;text-transform:uppercase;letter-spacing:1px">Lessons Learned</div></div>
  </div>
</div>""", unsafe_allow_html=True)

tab_journal, tab_wins, tab_lessons, tab_tips, tab_history = st.tabs([
    "✍️ Journal", "🏆 Log a Win", "💡 Lessons", "🧭 Tips & Guidance", "📅 History"])

# ══════════════════════ JOURNAL ══════════════════════════════════════════════
with tab_journal:
    existing_entry = get1("SELECT id,content,mood,tags FROM journal_entries WHERE date=?", (str(today),))
    st.markdown(f'<div class="label-mono">Today — {today.strftime("%A, %B %-d, %Y")}</div>', unsafe_allow_html=True)

    with st.form("journal_form"):
        jc1, jc2 = st.columns([3,1])
        with jc1:
            j_date    = st.date_input("Date", value=today)
            j_content = st.text_area(
                "Entry",
                value=existing_entry[1] if existing_entry else "",
                height=280,
                placeholder="What happened today? What are you thinking about? What are you working through?\n\nStream of consciousness is fine. This is your space."
            )
        with jc2:
            j_mood = st.slider("Mood", 1, 10,
                               int(existing_entry[2]) if existing_entry and existing_entry[2] else 7)
            mood_label = MOOD_LABELS.get(j_mood, "")
            st.markdown(f'<div style="text-align:center;font-size:1.5rem;margin:.3rem 0">{mood_label}</div>', unsafe_allow_html=True)
            j_tags = st.text_area("Tags", value=existing_entry[3] if existing_entry and existing_entry[3] else "",
                                   height=80, placeholder="grateful, focused, breakthrough, struggle...")

        if st.form_submit_button("💾 Save Entry"):
            if j_content.strip():
                run_q("""INSERT INTO journal_entries (date,content,mood,tags)
                         VALUES (?,?,?,?)
                         ON CONFLICT(date) DO UPDATE SET
                         content=excluded.content,mood=excluded.mood,tags=excluded.tags""",
                      (str(j_date), j_content.strip(), j_mood, j_tags.strip()))
                st.success("Entry saved."); st.rerun()

    # Mood trend chart
    mood_data = get_q("SELECT date,mood FROM journal_entries WHERE mood IS NOT NULL ORDER BY date DESC LIMIT 30")
    if len(mood_data) >= 3:
        mood_data = list(reversed(mood_data))
        fig = go.Figure(go.Scatter(
            x=[r[0] for r in mood_data], y=[r[1] for r in mood_data],
            mode="lines+markers",
            line=dict(color="#c4a882", width=2),
            marker=dict(size=7, color=[r[1] for r in mood_data],
                        colorscale=[[0,"#8b4049"],[0.5,"#d4681e"],[1,"#7a8c6e"]],
                        cmin=1, cmax=10, showscale=False),
            fill="tozeroy", fillcolor="rgba(196,168,130,0.05)"
        ))
        fig.add_hline(y=7, line_dash="dot", line_color="#7a8c6e", opacity=0.4,
                      annotation_text="Good baseline", annotation_font_color="#7a8c6e")
        fig.update_layout(
            paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
            font=dict(color="#f0e6d3", family="Space Mono"),
            yaxis=dict(title="Mood", range=[0,10.5], gridcolor="#2d2520",
                       tickvals=list(range(1,11))),
            xaxis=dict(color="#9a8878"),
            margin=dict(l=10,r=10,t=20,b=10), height=200,
            title=dict(text="Mood Trend (30d)", font=dict(color="#c4a882", family="Playfair Display"))
        )
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════ LOG A WIN ════════════════════════════════════════════
with tab_wins:
    st.markdown("### 🏆 Log a Win")
    st.markdown('<div style="font-size:.8rem;color:#9a8878;margin-bottom:.5rem">A win is anything worth acknowledging — big or small. Progress is progress.</div>', unsafe_allow_html=True)

    with st.form("log_win"):
        wc1,wc2 = st.columns(2)
        with wc1:
            w_date   = st.date_input("Date", value=today)
            w_title  = st.text_input("Win *", placeholder="e.g. Hit 3 plates on squat / Got an A on the exam")
            w_cat    = st.selectbox("Category", WIN_CATS)
        with wc2:
            w_impact = st.slider("Impact / Significance", 1, 5, 3,
                                  help="1=small step, 3=solid progress, 5=major milestone")
            impact_stars = "★" * w_impact + "☆" * (5 - w_impact)
            st.markdown(f'<div style="font-size:1.1rem;color:#c4a882;margin-top:.5rem">{impact_stars}</div>', unsafe_allow_html=True)
            w_desc = st.text_area("Description / Context", height=80)
        if st.form_submit_button("🏆 Log Win"):
            if w_title.strip():
                run_q("INSERT INTO wins (date,title,description,category,impact) VALUES (?,?,?,?,?)",
                      (str(w_date), w_title.strip(), w_desc.strip(), w_cat, w_impact))
                st.success("Win logged! Keep it up."); st.rerun()
            else:
                st.error("Title required.")

    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    # Recent wins
    cat_filter = st.selectbox("Filter by category", ["all"] + WIN_CATS, key="win_cat_filter")
    where      = "" if cat_filter=="all" else f"WHERE category='{cat_filter}'"
    wins       = get_q(f"SELECT id,date,title,description,category,impact FROM wins {where} ORDER BY date DESC, id DESC LIMIT 50")

    cat_colors = {
        "fitness":"#d4681e","academic":"#c4a882","music":"#7a8c6e",
        "finance":"#f0e6d3","personal":"#9a8878","creative":"#8b4049",
        "work":"#c4a882","social":"#7a8c6e","health":"#d4681e"
    }
    for w in wins:
        wid,wdate,wtitle,wdesc,wcat,wimpact = w
        cc     = cat_colors.get(wcat,"#9a8878")
        stars  = "★" * (wimpact or 3) + "☆" * (5-(wimpact or 3))
        col_w, col_wd = st.columns([5,1])
        with col_w:
            st.markdown(f"""
<div class="vinyl-card" style="border-left-color:{cc};padding:.5rem 1.1rem;margin:.25rem 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="font-size:.88rem;color:#f0e6d3">{wtitle}</span>
    <span style="color:#c4a882;font-size:.85rem">{stars}</span>
  </div>
  <div style="font-size:.68rem;color:#9a8878;margin-top:.15rem">
    {wdate} · <span style="color:{cc}">{wcat}</span>
    {f' · {wdesc[:80]}' if wdesc else ''}
  </div>
</div>""", unsafe_allow_html=True)
        with col_wd:
            if st.button("🗑", key=f"wdel_{wid}"):
                run_q("DELETE FROM wins WHERE id=?", (wid,)); st.rerun()

    # Wins by category chart
    if wins:
        cat_data = get_q("SELECT category, COUNT(*) FROM wins GROUP BY category ORDER BY 2 DESC")
        fig = go.Figure(go.Bar(
            x=[r[0] for r in cat_data], y=[r[1] for r in cat_data],
            marker_color=[cat_colors.get(r[0],"#9a8878") for r in cat_data],
            marker_line_width=0))
        fig.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                          font=dict(color="#f0e6d3", family="Space Mono"),
                          yaxis=dict(gridcolor="#2d2520"), xaxis=dict(color="#9a8878"),
                          margin=dict(l=10,r=10,t=10,b=10), height=200)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════ LESSONS LEARNED ══════════════════════════════════════
with tab_lessons:
    st.markdown("### 💡 Lessons Learned")
    st.markdown('<div style="font-size:.8rem;color:#9a8878;margin-bottom:.5rem">Capture insights while they\'re fresh. This is your personal playbook — the lessons that actually cost you something to learn.</div>', unsafe_allow_html=True)

    with st.form("add_lesson"):
        lc1,lc2 = st.columns(2)
        with lc1:
            l_date    = st.date_input("Date", value=today)
            l_lesson  = st.text_area("The Lesson *", height=100,
                                      placeholder="What did you learn? State it clearly, like you're teaching someone.")
        with lc2:
            l_context = st.text_area("Context / Story", height=100,
                                      placeholder="What happened? What situation taught you this?")
            l_tags    = st.text_input("Tags", placeholder="discipline, money, relationships...")
        if st.form_submit_button("Save Lesson"):
            if l_lesson.strip():
                run_q("INSERT INTO lessons_learned (date,lesson,context,tags) VALUES (?,?,?,?)",
                      (str(l_date), l_lesson.strip(), l_context.strip(), l_tags.strip()))
                st.success("Lesson captured."); st.rerun()

    tag_search = st.text_input("Search lessons", placeholder="Search by lesson text or tag...")
    lessons    = get_q("SELECT id,date,lesson,context,tags FROM lessons_learned ORDER BY date DESC, id DESC")
    if tag_search:
        lessons = [l for l in lessons if
                   tag_search.lower() in (l[2] or "").lower() or
                   tag_search.lower() in (l[4] or "").lower()]

    for l in lessons:
        lid,ldate,llesson,lcontext,ltags = l
        col_l, col_ld = st.columns([5,1])
        with col_l:
            tags_html = ""
            if ltags:
                tags_html = " ".join(f'<span class="badge badge-medium">{t.strip()}</span>' for t in ltags.split(",") if t.strip())
            st.markdown(f"""
<div class="vinyl-card vinyl-card-gold" style="padding:.6rem 1.2rem;margin:.3rem 0">
  <div style="font-size:.88rem;color:#f0e6d3;font-style:italic">"{llesson}"</div>
  {f'<div style="font-size:.72rem;color:#9a8878;margin-top:.3rem">{lcontext[:120]}{"…" if len(lcontext or "")>120 else ""}</div>' if lcontext else ''}
  <div style="margin-top:.4rem;font-size:.65rem;color:#9a8878">{ldate} &nbsp; {tags_html}</div>
</div>""", unsafe_allow_html=True)
        with col_ld:
            if st.button("🗑", key=f"ldel_{lid}"):
                run_q("DELETE FROM lessons_learned WHERE id=?", (lid,)); st.rerun()

# ══════════════════════ TIPS & GUIDANCE ══════════════════════════════════════
with tab_tips:
    st.markdown("### 🧭 Principles & Guidance")

    PRINCIPLES = [
        ("On Discipline", "orange",
         "You don't rise to the level of your goals — you fall to the level of your systems. Build the system first. The results are downstream of the process.",
         "James Clear / Atomic Habits"),
        ("On Consistency", "sage",
         "A mediocre workout done consistently beats a perfect workout done occasionally. Show up, especially on the days you don't feel like it — those days build the most character.",
         "Jarvis"),
        ("On Investment Patience", "gold",
         "The market is a device for transferring money from the impatient to the patient. Your edge isn't information — it's time horizon and emotional discipline.",
         "Warren Buffett (paraphrased)"),
        ("On Learning", "orange",
         "The best way to learn is to teach. After every study session, close the book and explain the concept out loud as if teaching a class. If you can't explain it simply, you don't understand it yet.",
         "Feynman Technique"),
        ("On Music Practice", "sage",
         "Slow practice is fast progress. Play at the tempo where you make zero mistakes, then gradually increase. Practicing mistakes just makes you better at making mistakes.",
         "Traditional pedagogy"),
        ("On Journaling", "gold",
         "The unexamined life is not worth living. Write every day — not because it's useful (though it is), but because it forces you to think clearly about what actually happened and what you actually believe.",
         "Socrates / Stoic tradition"),
        ("On the Long Game", "orange",
         "Most people overestimate what they can do in a day and underestimate what they can do in a year. Give your compounding more time to work.",
         "Jarvis"),
        ("On Hard Days", "sage",
         "When you don't want to — that's the point. When it's hard — that's the growth. The discomfort is the signal that you're in the right place. Lean into it.",
         "Jarvis"),
    ]

    variant_map = {"orange": "", "sage": "vinyl-card-sage", "gold": "vinyl-card-gold"}
    for title, variant, text, source in PRINCIPLES:
        st.markdown(f"""
<div class="vinyl-card {variant_map.get(variant,'')} " style="padding:.7rem 1.3rem;margin:.4rem 0">
  <div style="font-family:'Playfair Display',serif;font-size:.92rem;color:#c4a882;margin-bottom:.3rem">{title}</div>
  <div style="font-size:.83rem;color:#f0e6d3;font-style:italic;line-height:1.5">"{text}"</div>
  <div style="font-size:.65rem;color:#9a8878;margin-top:.4rem">— {source}</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ✏️ Add Your Own Principle")
    with st.form("add_principle"):
        ppc1,ppc2 = st.columns(2)
        with ppc1: pp_title = st.text_input("Title / Theme")
        with ppc2: pp_source = st.text_input("Source / Author")
        pp_text = st.text_area("The Principle", height=80)
        if st.form_submit_button("Save Principle"):
            if pp_text.strip():
                st.session_state.setdefault("custom_principles", []).append({
                    "title": pp_title, "text": pp_text, "source": pp_source
                })
                st.success("Saved for this session. Add to your principles list in the code to make permanent.")

    for cp in st.session_state.get("custom_principles", []):
        st.markdown(f"""
<div class="vinyl-card vinyl-card-gold" style="padding:.6rem 1.2rem;margin:.3rem 0">
  <div style="font-family:'Playfair Display',serif;font-size:.88rem;color:#c4a882">{cp.get('title','')}</div>
  <div style="font-size:.82rem;color:#f0e6d3;font-style:italic">"{cp.get('text','')}"</div>
  <div style="font-size:.65rem;color:#9a8878">— {cp.get('source','')}</div>
</div>""", unsafe_allow_html=True)

# ══════════════════════ HISTORY ══════════════════════════════════════════════
with tab_history:
    st.markdown("### 📅 Journal Archive")
    month_filter = st.selectbox("Month",
        ["All time"] + sorted(set(r[0][:7] for r in get_q("SELECT date FROM journal_entries ORDER BY date DESC")), reverse=True))

    if month_filter == "All time":
        entries = get_q("SELECT date,content,mood,tags FROM journal_entries ORDER BY date DESC")
    else:
        entries = get_q("SELECT date,content,mood,tags FROM journal_entries WHERE date LIKE ? ORDER BY date DESC",
                        (f"{month_filter}%",))

    for e in entries:
        edate,econtent,emood,etags = e
        mood_label = MOOD_LABELS.get(emood or 0, "")
        preview    = (econtent or "")[:150] + "…" if len(econtent or "") > 150 else econtent or ""
        mood_color = "#7a8c6e" if (emood or 0) >= 7 else "#d4681e" if (emood or 0) >= 5 else "#8b4049"
        with st.expander(f"{edate}   {mood_label}"):
            st.markdown(f'<div style="font-size:.82rem;color:#f0e6d3;line-height:1.7;white-space:pre-wrap">{econtent or ""}</div>', unsafe_allow_html=True)
            if etags:
                tags_html = " ".join(f'<span class="badge badge-medium">{t.strip()}</span>' for t in etags.split(",") if t.strip())
                st.markdown(tags_html, unsafe_allow_html=True)

conn.close()
