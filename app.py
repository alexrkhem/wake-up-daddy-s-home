"""
Dashboard Home — Jarvis Personal OS
Indie Record Shop Aesthetic
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="Dashboard — Jarvis",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
import datetime, json

init_db()
apply_styles()
render_jarvis_sidebar()

today = datetime.date.today()
conn  = get_connection()

def q(sql, params=()):
    cur = conn.cursor(); cur.execute(sql, params); return cur.fetchall()
def q1(sql, params=()):
    cur = conn.cursor(); cur.execute(sql, params); r = cur.fetchone(); return r[0] if r else 0

page_header("🎵", "Personal Dashboard", "Jarvis OS — v1.0")

# ── Overview Stats Row ──────────────────────────────────────────────────────
c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1:
    due = q1("SELECT COUNT(*) FROM todos WHERE status!='done' AND target_date<?", (str(today),))
    total_open = q1("SELECT COUNT(*) FROM todos WHERE status!='done'")
    st.metric("Open Todos", total_open, delta=f"-{due} overdue" if due else None, delta_color="inverse")
with c2:
    sleep_r = q("SELECT quality, duration_hours FROM sleep_log ORDER BY date DESC LIMIT 1")
    if sleep_r:
        st.metric("Last Sleep", f"{sleep_r[0][1] or 0:.1f}h", f"Quality {sleep_r[0][0]}/10")
    else:
        st.metric("Last Sleep", "—", "No data")
with c3:
    workouts_week = q1("SELECT COUNT(*) FROM workouts WHERE date>=?",
                       (str(today - datetime.timedelta(days=7)),))
    st.metric("Workouts / 7d", workouts_week)
with c4:
    cal = q1("SELECT calories FROM nutrition_log ORDER BY date DESC LIMIT 1")
    st.metric("Last Calories", f"{cal or 0:,.0f} kcal")
with c5:
    music_week = q1("SELECT COALESCE(SUM(duration_mins),0) FROM music_sessions WHERE date>=?",
                    (str(today - datetime.timedelta(days=7)),))
    st.metric("Music / 7d", f"{music_week//60}h {music_week%60}m")
with c6:
    wins_month = q1("SELECT COUNT(*) FROM wins WHERE date>=?",
                    (str(today.replace(day=1)),))
    st.metric("Wins this Month", wins_month)

st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)

# ── Main Grid ───────────────────────────────────────────────────────────────
col_a, col_b, col_c = st.columns([1.2, 1.2, 0.9])

with col_a:
    st.markdown("### 📋 Today's Priority Todos")
    todos = q("""SELECT title, priority, target_date, status FROM todos
                 WHERE status!='done' ORDER BY
                 CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                 target_date LIMIT 6""")
    if todos:
        for t in todos:
            p_color = {"high":"#e08090","medium":"#d4681e","low":"#7a8c6e"}.get(t[1],"#9a8878")
            overdue = t[2] and t[2] < str(today)
            over_html = ' <span style="color:#8b4049;font-size:.65rem">OVERDUE</span>' if overdue else ""
            st.markdown(f"""<div class="vinyl-card" style="border-left-color:{p_color};padding:.5rem 1rem;margin:.25rem 0">
<span style="font-size:.8rem;color:#f0e6d3">{t[0]}</span>{over_html}
<br><span style="font-size:.65rem;color:#9a8878">{t[2] or 'No date'} · {t[1]}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="vinyl-card vinyl-card-sage" style="font-size:.85rem;color:#7a8c6e">All clear — no open todos ✓</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown("### 📅 Upcoming Assignments")
    assigns = q("""SELECT a.title, c.name, a.due_date, a.priority FROM assignments a
                   LEFT JOIN courses c ON a.course_id=c.id
                   WHERE a.status!='done' AND (a.due_date IS NULL OR a.due_date>=?)
                   ORDER BY a.due_date LIMIT 5""", (str(today),))
    if assigns:
        for a in assigns:
            days_left = ""
            if a[2]:
                d = (datetime.date.fromisoformat(a[2]) - today).days
                days_left = f' · <span style="color:{"#e08090" if d<=2 else "#d4681e" if d<=7 else "#9a8878"}">{d}d</span>'
            st.markdown(f"""<div class="vinyl-card vinyl-card-gold" style="padding:.5rem 1rem;margin:.2rem 0">
<span style="font-size:.8rem">{a[0]}</span>{days_left}
<br><span style="font-size:.65rem;color:#9a8878">{a[1] or 'No course'} · {a[2] or '—'}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="vinyl-card vinyl-card-sage" style="font-size:.85rem;color:#7a8c6e">No upcoming assignments ✓</div>', unsafe_allow_html=True)

with col_b:
    st.markdown("### 📈 Portfolio Snapshot")
    holdings = q("SELECT symbol, shares, avg_cost FROM portfolio_holdings LIMIT 10")
    if holdings:
        try:
            import yfinance as yf
            symbols = [h[0] for h in holdings]
            tickers = yf.download(symbols, period="1d", auto_adjust=True, progress=False)
            total_val = 0.0; total_cost = 0.0
            rows = []
            for sym, shares, avg_cost in holdings:
                try:
                    if len(symbols) == 1:
                        price = float(tickers["Close"].iloc[-1])
                    else:
                        price = float(tickers["Close"][sym].iloc[-1])
                    val  = price * (shares or 0)
                    cost = (avg_cost or 0) * (shares or 0)
                    pct  = ((val - cost) / cost * 100) if cost else 0
                    total_val  += val
                    total_cost += cost
                    rows.append((sym, f"{price:.2f}", f"{val:,.0f}", f"{pct:+.1f}%"))
                except Exception:
                    rows.append((sym, "—", "—", "—"))
            for sym, price, val, pct in rows[:8]:
                color = "#7a8c6e" if "+" in pct else "#8b4049"
                st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:.3rem .5rem;
background:#23201c;border-radius:3px;margin:.15rem 0;font-size:.78rem">
<span style="color:#f0e6d3;font-family:'Space Mono',monospace">{sym}</span>
<span style="color:#9a8878">${price}</span>
<span style="color:{color};font-weight:700">{pct}</span>
</div>""", unsafe_allow_html=True)
            total_pct = ((total_val - total_cost) / total_cost * 100) if total_cost else 0
            st.markdown(f'<div style="margin-top:.5rem;font-size:.7rem;color:#c4a882">Total: ${total_val:,.0f} &nbsp; <span style="color:{"#7a8c6e" if total_pct>=0 else "#8b4049"}">{total_pct:+.1f}%</span></div>', unsafe_allow_html=True)
        except ImportError:
            for sym, shares, avg in holdings:
                st.markdown(f'<div style="font-size:.8rem;padding:.2rem 0">{sym} — {shares} shares @ ${avg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="vinyl-card" style="font-size:.85rem;color:#9a8878">No holdings logged yet. Add them in the Investments page.</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown("### 🎵 Music Practice This Week")
    music_data = q("""SELECT instrument, SUM(duration_mins) as mins
                      FROM music_sessions WHERE date>=?
                      GROUP BY instrument""", (str(today - datetime.timedelta(days=7)),))
    if music_data:
        for inst, mins in music_data:
            mins = mins or 0
            pct  = min(int(mins / 300 * 100), 100)
            color = "#d4681e" if inst == "guitar" else "#c4a882"
            st.markdown(f"""<div style="margin:.3rem 0">
<div style="display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:.2rem">
  <span style="color:#f0e6d3;text-transform:capitalize">{inst}</span>
  <span style="color:#9a8878">{mins//60}h {mins%60}m</span>
</div>
<div style="background:#2d2520;border-radius:2px;height:5px">
  <div style="background:{color};width:{pct}%;height:5px;border-radius:2px"></div>
</div></div>""", unsafe_allow_html=True)
    else:
        st.markdown('<span style="font-size:.8rem;color:#9a8878">No sessions logged this week.</span>', unsafe_allow_html=True)

with col_c:
    st.markdown("### 💤 Sleep Last 7 Days")
    sleep7 = q("""SELECT date, duration_hours, quality FROM sleep_log
                  ORDER BY date DESC LIMIT 7""")
    for s in sleep7:
        q_color = "#7a8c6e" if (s[2] or 0)>=7 else "#d4681e" if (s[2] or 0)>=5 else "#8b4049"
        st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:.25rem .5rem;
font-size:.75rem;background:#23201c;border-radius:3px;margin:.12rem 0">
<span style="color:#9a8878">{s[0]}</span>
<span style="color:#c4a882">{s[1] or 0:.1f}h</span>
<span style="color:{q_color}">{s[2] or '—'}/10</span>
</div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown("### 🏆 Recent Wins")
    wins = q("SELECT date, title, category FROM wins ORDER BY date DESC LIMIT 5")
    streak_days = 0
    if wins:
        d = today
        for w in wins:
            if w[0] >= str(today - datetime.timedelta(days=streak_days+1)):
                streak_days += 1
        for w in wins:
            cat_color = {"fitness":"#d4681e","academic":"#c4a882","music":"#7a8c6e",
                         "finance":"#f0e6d3"}.get(w[2],"#9a8878")
            st.markdown(f"""<div class="vinyl-card" style="padding:.4rem .8rem;margin:.15rem 0;border-left-color:{cat_color}">
<span style="font-size:.8rem;color:#f0e6d3">{w[1]}</span>
<br><span style="font-size:.65rem;color:#9a8878">{w[0]} · {w[2] or 'general'}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown('<span style="font-size:.8rem;color:#9a8878">Log your first win in the Journal page.</span>', unsafe_allow_html=True)

    st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)
    st.markdown(f"""<div style="text-align:center;padding:.5rem;background:#23201c;border-radius:4px">
<div style="font-family:'Playfair Display',serif;font-size:2.5rem;color:#c4a882;line-height:1">{wins.__len__()}</div>
<div style="font-size:.65rem;color:#9a8878;letter-spacing:2px;text-transform:uppercase">Total Wins</div>
</div>""", unsafe_allow_html=True)

conn.close()
st.markdown('<div style="height:2rem"></div>', unsafe_allow_html=True)
st.markdown('<div style="font-size:.6rem;color:#3d3028;text-align:center;letter-spacing:2px">JARVIS PERSONAL OS · INDIE EDITION · {}</div>'.format(today.strftime("%B %Y")), unsafe_allow_html=True)
