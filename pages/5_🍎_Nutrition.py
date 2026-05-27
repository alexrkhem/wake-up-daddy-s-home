import streamlit as st, sys, datetime, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
st.set_page_config(page_title="Nutrition · Jarvis", page_icon="🍎", layout="wide")
from database import init_db, get_connection
from styles import apply_styles, page_header
from components.jarvis import render_jarvis_sidebar
import plotly.graph_objects as go
import pandas as pd
init_db(); apply_styles(); render_jarvis_sidebar()

conn  = get_connection()
today = datetime.date.today()
def run_q(sql,p=()): conn.execute(sql,p); conn.commit()
def get_q(sql,p=()): c=conn.cursor(); c.execute(sql,p); return c.fetchall()
def get1(sql,p=()):  c=conn.cursor(); c.execute(sql,p); r=c.fetchone(); return r

page_header("🍎", "Nutrition Tracker", "cronometer · macros · schedule")

# Macro targets (user can adjust)
CALS_TARGET  = 2700
PROTEIN_TARGET = 180
CARBS_TARGET   = 310
FAT_TARGET     = 75

# ── Stats ────────────────────────────────────────────────────────────────────
last = get1("SELECT date,calories,protein_g,carbs_g,fat_g FROM nutrition_log ORDER BY date DESC LIMIT 1")
avg7_cals = get1("SELECT AVG(calories) FROM nutrition_log WHERE date>=?",
                 (str(today - datetime.timedelta(days=7)),))

c1,c2,c3,c4 = st.columns(4)
c1.metric("Last Logged Calories",  f"{last[1] or 0:,.0f}" if last else "—",
          f"on {last[0]}" if last else "No data")
c2.metric("Protein (last log)",    f"{last[2] or 0:.0f}g" if last else "—",
          f"Goal: {PROTEIN_TARGET}g")
c3.metric("7-Day Avg Calories",    f"{avg7_cals[0] or 0:,.0f}" if avg7_cals and avg7_cals[0] else "—")
c4.metric("Days Tracked",          get1("SELECT COUNT(*) FROM nutrition_log")[0])

st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)

tab_import, tab_today, tab_schedule, tab_history = st.tabs([
    "📂  Import Cronometer CSV", "📊  Today's Macros", "🕐  Eating Schedule", "📈  History"])

# ══════════════════════ CSV IMPORT ══════════════════════════════════════════
with tab_import:
    st.markdown("### Import from Cronometer")
    st.markdown("""<div class="vinyl-card vinyl-card-gold" style="font-size:.82rem">
<b>How to export from Cronometer:</b><br>
1. Open Cronometer (web or app) → <b>Diary</b><br>
2. Click <b>Export</b> (or go to Account → Export Data → Daily Nutrition)<br>
3. Select <b>Diary CSV</b> or <b>Daily Summary CSV</b><br>
4. Upload the file below
</div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload Cronometer CSV Export", type=["csv"], key="cron_csv")
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            st.markdown("**Preview:**")
            st.dataframe(df.head(10), use_container_width=True)

            # Try to auto-detect columns
            col_map = {}
            col_lower = {c.lower().strip(): c for c in df.columns}

            date_candidates    = ["date","day"]
            cal_candidates     = ["calories","energy (kcal)","energy","kcal"]
            protein_candidates = ["protein (g)","protein","protein_g"]
            carb_candidates    = ["carbs (g)","carbohydrates (g)","carbs","net carbs (g)","carbohydrates"]
            fat_candidates     = ["fat (g)","total fat (g)","fat","fat_g"]
            fiber_candidates   = ["fiber (g)","dietary fiber (g)","fiber"]

            def find_col(candidates, col_lower):
                for c in candidates:
                    if c in col_lower: return col_lower[c]
                return None

            date_col    = find_col(date_candidates, col_lower)
            cal_col     = find_col(cal_candidates, col_lower)
            protein_col = find_col(protein_candidates, col_lower)
            carb_col    = find_col(carb_candidates, col_lower)
            fat_col     = find_col(fat_candidates, col_lower)
            fiber_col   = find_col(fiber_candidates, col_lower)

            st.markdown("**Column Mapping (auto-detected — adjust if needed):**")
            mc1,mc2,mc3 = st.columns(3)
            all_cols = ["— None —"] + list(df.columns)
            with mc1:
                date_sel    = st.selectbox("Date column",    all_cols, index=all_cols.index(date_col) if date_col and date_col in all_cols else 0)
                cal_sel     = st.selectbox("Calories",       all_cols, index=all_cols.index(cal_col)  if cal_col  and cal_col  in all_cols else 0)
            with mc2:
                protein_sel = st.selectbox("Protein (g)",   all_cols, index=all_cols.index(protein_col) if protein_col and protein_col in all_cols else 0)
                carb_sel    = st.selectbox("Carbs (g)",      all_cols, index=all_cols.index(carb_col)    if carb_col    and carb_col    in all_cols else 0)
            with mc3:
                fat_sel     = st.selectbox("Fat (g)",        all_cols, index=all_cols.index(fat_col)    if fat_col    and fat_col    in all_cols else 0)
                fiber_sel   = st.selectbox("Fiber (g)",      all_cols, index=all_cols.index(fiber_col)  if fiber_col  and fiber_col  in all_cols else 0)

            if st.button("📥 Import into Dashboard", type="primary"):
                if date_sel == "— None —" or cal_sel == "— None —":
                    st.error("Date and Calories columns are required.")
                else:
                    imported = 0
                    errors   = 0
                    for _, row in df.iterrows():
                        try:
                            raw_date = str(row[date_sel]).strip()
                            # Handle various date formats
                            for fmt in ["%Y-%m-%d","%m/%d/%Y","%d/%m/%Y","%Y/%m/%d"]:
                                try:
                                    parsed_date = datetime.datetime.strptime(raw_date, fmt).date()
                                    break
                                except ValueError:
                                    continue
                            else:
                                errors += 1; continue

                            def safe_float(col):
                                if col == "— None —": return None
                                try: return float(str(row[col]).replace(",",""))
                                except: return None

                            run_q("""INSERT INTO nutrition_log (date,calories,protein_g,carbs_g,fat_g,fiber_g,source)
                                     VALUES (?,?,?,?,?,?,?)
                                     ON CONFLICT(date) DO UPDATE SET
                                     calories=excluded.calories,protein_g=excluded.protein_g,
                                     carbs_g=excluded.carbs_g,fat_g=excluded.fat_g,
                                     fiber_g=excluded.fiber_g,source=excluded.source""",
                                  (str(parsed_date), safe_float(cal_sel), safe_float(protein_sel),
                                   safe_float(carb_sel), safe_float(fat_sel), safe_float(fiber_sel),
                                   "cronometer_csv"))
                            imported += 1
                        except Exception:
                            errors += 1
                    st.success(f"Imported {imported} days of data.{f' ({errors} rows skipped)' if errors else ''}")
                    st.rerun()
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")

    st.markdown("### Manual Entry")
    with st.form("manual_nutrition"):
        nc1,nc2,nc3 = st.columns(3)
        with nc1:
            n_date  = st.date_input("Date", value=today)
            n_cals  = st.number_input("Calories", 0, 10000, 2000, 50)
        with nc2:
            n_prot  = st.number_input("Protein (g)", 0.0, 500.0, 150.0, 5.0)
            n_carbs = st.number_input("Carbs (g)",   0.0, 1000.0, 250.0, 5.0)
        with nc3:
            n_fat   = st.number_input("Fat (g)",   0.0, 500.0, 70.0, 2.0)
            n_fiber = st.number_input("Fiber (g)", 0.0, 200.0, 25.0, 1.0)
        n_notes = st.text_input("Notes")
        if st.form_submit_button("Save Entry"):
            run_q("""INSERT INTO nutrition_log (date,calories,protein_g,carbs_g,fat_g,fiber_g,notes,source)
                     VALUES (?,?,?,?,?,?,?,?)
                     ON CONFLICT(date) DO UPDATE SET calories=excluded.calories,protein_g=excluded.protein_g,
                     carbs_g=excluded.carbs_g,fat_g=excluded.fat_g,fiber_g=excluded.fiber_g,
                     notes=excluded.notes,source=excluded.source""",
                  (str(n_date), n_cals, n_prot, n_carbs, n_fat, n_fiber, n_notes, "manual"))
            st.success("Saved!"); st.rerun()

# ══════════════════════ TODAY'S MACROS ══════════════════════════════════════
with tab_today:
    log_sel = st.date_input("View date", value=today, key="view_date")
    row     = get1("SELECT calories,protein_g,carbs_g,fat_g,fiber_g,source FROM nutrition_log WHERE date=?",
                   (str(log_sel),))

    if row:
        cals, prot, carbs, fat, fiber, source = row

        def macro_bar(label, actual, target, color):
            actual  = actual or 0
            pct     = min(int(actual / target * 100), 100) if target else 0
            over    = actual > target * 1.05
            bar_col = "#8b4049" if over else color
            st.markdown(f"""
<div style="margin:.5rem 0">
  <div style="display:flex;justify-content:space-between;font-size:.78rem;margin-bottom:.2rem">
    <span style="color:#f0e6d3">{label}</span>
    <span style="color:{bar_col};font-family:'Space Mono',monospace">{actual:.0f} / {target}</span>
  </div>
  <div style="background:#2d2520;border-radius:3px;height:8px">
    <div style="background:{bar_col};width:{pct}%;height:8px;border-radius:3px;transition:width .3s"></div>
  </div>
  <div style="font-size:.65rem;color:#9a8878;text-align:right">{pct}%</div>
</div>""", unsafe_allow_html=True)

        bc1, bc2 = st.columns([1, 1])
        with bc1:
            macro_bar("🔥 Calories",  cals,  CALS_TARGET,    "#d4681e")
            macro_bar("🥩 Protein",   prot,  PROTEIN_TARGET, "#c4a882")
            macro_bar("🌾 Carbs",     carbs, CARBS_TARGET,   "#7a8c6e")
            macro_bar("🧈 Fat",       fat,   FAT_TARGET,     "#8b4049")
        with bc2:
            if prot and carbs and fat:
                total_cal_from_macros = (prot * 4) + (carbs * 4) + (fat * 9)
                labels = ["Protein", "Carbs", "Fat"]
                values = [prot * 4, carbs * 4, fat * 9]
                colors = ["#c4a882", "#7a8c6e", "#8b4049"]
                fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55,
                                       marker=dict(colors=colors, line=dict(color="#1a1814", width=2))))
                fig.update_layout(paper_bgcolor="#1a1814", font=dict(color="#f0e6d3"),
                                  margin=dict(l=0,r=0,t=0,b=0), height=220,
                                  legend=dict(bgcolor="rgba(0,0,0,0)"),
                                  annotations=[dict(text=f"{cals:.0f}<br>kcal",
                                                    font=dict(size=14, color="#d4681e",
                                                              family="Playfair Display"),
                                                    showarrow=False)])
                st.plotly_chart(fig, use_container_width=True)
            st.markdown(f'<div class="label-mono">Source: {source}</div>', unsafe_allow_html=True)
            if fiber: st.markdown(f'<div style="font-size:.8rem;color:#9a8878">Fiber: {fiber:.0f}g</div>', unsafe_allow_html=True)
    else:
        st.info(f"No nutrition data for {log_sel}. Import from Cronometer or add a manual entry.")

# ══════════════════════ EATING SCHEDULE ═════════════════════════════════════
with tab_schedule:
    st.markdown("### 🕐 Scheduled Eating Routine")
    schedule = get_q("SELECT id,meal_name,scheduled_time,description,approx_calories FROM eating_schedule WHERE active=1 ORDER BY scheduled_time")
    total_sched_cals = sum(r[4] or 0 for r in schedule)

    for meal in schedule:
        mid, mname, mtime, mdesc, mcals = meal
        st.markdown(f"""
<div class="vinyl-card" style="padding:.55rem 1.2rem;margin:.3rem 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span style="font-size:.95rem;color:#f0e6d3">{mname}</span>
      <span style="font-size:.7rem;color:#9a8878;margin-left:.5rem">{mdesc or ''}</span>
    </div>
    <div style="text-align:right">
      <div style="font-family:'Space Mono',monospace;font-size:.9rem;color:#d4681e">{mtime or '—'}</div>
      <div style="font-size:.65rem;color:#9a8878">~{mcals or 0} kcal</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="label-mono" style="margin-top:.5rem">Total scheduled: ~{total_sched_cals} kcal/day</div>', unsafe_allow_html=True)

    st.markdown('<div class="vinyl-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ✏️ Edit Schedule")
    with st.form("add_meal"):
        mc1,mc2,mc3 = st.columns(3)
        with mc1: meal_n = st.text_input("Meal Name")
        with mc2: meal_t = st.text_input("Time", placeholder="e.g. 7:30 AM")
        with mc3: meal_c = st.number_input("~Calories", 0, 2000, 400, 50)
        meal_d = st.text_input("Description")
        if st.form_submit_button("Add Meal"):
            if meal_n.strip():
                run_q("INSERT INTO eating_schedule (meal_name,scheduled_time,description,approx_calories) VALUES (?,?,?,?)",
                      (meal_n.strip(), meal_t.strip(), meal_d.strip(), meal_c))
                st.rerun()

# ══════════════════════ HISTORY ════════════════════════════════════════════
with tab_history:
    history = get_q("SELECT date,calories,protein_g,carbs_g,fat_g FROM nutrition_log ORDER BY date DESC LIMIT 60")
    if len(history) >= 3:
        history = list(reversed(history))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[r[0] for r in history], y=[r[1] or 0 for r in history],
                                  name="Calories", line=dict(color="#d4681e",width=2), fill="tozeroy",
                                  fillcolor="rgba(212,104,30,0.1)"))
        fig.add_hline(y=CALS_TARGET, line_dash="dash", line_color="#7a8c6e",
                      annotation_text=f"Target: {CALS_TARGET}", annotation_font_color="#7a8c6e")
        fig.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                          font=dict(color="#f0e6d3", family="Space Mono"),
                          yaxis=dict(title="Calories", gridcolor="#2d2520"),
                          xaxis=dict(color="#9a8878"), margin=dict(l=10,r=10,t=10,b=10), height=260)
        st.plotly_chart(fig, use_container_width=True)

        # Macro trend
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=[r[0] for r in history], y=[r[2] or 0 for r in history],
                                   name="Protein", line=dict(color="#c4a882",width=1.5)))
        fig2.add_trace(go.Scatter(x=[r[0] for r in history], y=[r[3] or 0 for r in history],
                                   name="Carbs", line=dict(color="#7a8c6e",width=1.5)))
        fig2.add_trace(go.Scatter(x=[r[0] for r in history], y=[r[4] or 0 for r in history],
                                   name="Fat", line=dict(color="#8b4049",width=1.5)))
        fig2.update_layout(paper_bgcolor="#1a1814", plot_bgcolor="#1a1814",
                           font=dict(color="#f0e6d3", family="Space Mono"),
                           yaxis=dict(title="Grams", gridcolor="#2d2520"),
                           xaxis=dict(color="#9a8878"), legend=dict(bgcolor="rgba(0,0,0,0)"),
                           margin=dict(l=10,r=10,t=10,b=10), height=220)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Log at least 3 days to see history charts.")

conn.close()
